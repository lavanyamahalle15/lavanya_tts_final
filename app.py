from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
import os
import subprocess
import gc
import logging
import traceback
from functools import wraps, lru_cache
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/audio')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Increased to 32MB for Standard plan
app.config['MODEL_CACHE_SIZE'] = 4  # Cache size for models

# Ensure directories exist with proper permissions
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o755, exist_ok=True)
    # Make directory world-writable for Render environment
    os.chmod(app.config['UPLOAD_FOLDER'], 0o777)
    logger.info(f"Created directory with permissions: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    logger.error(f"Error creating directory: {str(e)}")

# Create a thread pool with more workers for Standard plan
executor = ThreadPoolExecutor(max_workers=4)

@lru_cache(maxsize=4)
def load_model(language, gender):
    # Your existing model loading code here
    pass

def cleanup_old_files(directory, max_age=7200):  # Increased to 2 hours
    try:
        current_time = time.time()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age:
                    os.remove(filepath)
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")

# --- Process timeout function ---
def process_tts(text, language, gender, alpha, output_file, inference_dir):
    """Process TTS in a separate function that doesn't need request context"""
    try:
        # Reduce text length for very long inputs to prevent timeouts
        if len(text) > 200:
            logger.warning("Long text detected, may cause timeout")
            
        cmd = [
            'python',
            'inference.py',
            '--sample_text', text,
            '--language', language,
            '--gender', gender,
            '--alpha', str(alpha),
            '--output_file', output_file
        ]
        
        logger.info(f"Running TTS command: {' '.join(cmd)}")
        logger.info(f"Working directory: {inference_dir}")
        
        process = subprocess.run(
            cmd,
            check=False,  # Don't raise immediately
            cwd=inference_dir,
            capture_output=True,
            text=True,
            timeout=120  # Increased timeout for longer processing
        )
        
        if process.returncode != 0:
            error_msg = f"TTS process failed with return code {process.returncode}.\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
            logger.error(error_msg)
            
            # Check if the inference directory exists
            if not os.path.exists(inference_dir):
                raise FileNotFoundError(f"Inference directory not found: {inference_dir}")
                
            # Check if inference.py exists
            inference_path = os.path.join(inference_dir, 'inference.py')
            if not os.path.exists(inference_path):
                raise FileNotFoundError(f"inference.py not found at: {inference_path}")
                
            raise subprocess.CalledProcessError(process.returncode, cmd, process.stdout, process.stderr)
            
        if not os.path.exists(output_file):
            logger.error("Output file was not generated")
            raise FileNotFoundError("Audio file was not generated")
            
        return True
            
    except subprocess.TimeoutExpired:
        logger.error("TTS process timed out")
        # Clean up any partial output file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                logger.error(f"Failed to clean up partial output file: {str(e)}")
        raise TimeoutError("Speech generation timed out. Please try with shorter text.")
    except Exception as e:
        logger.error(f"TTS processing error: {str(e)}")
        # Clean up any partial output file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as cleanup_err:
                logger.error(f"Failed to clean up partial output file: {str(cleanup_err)}")
        raise

def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get all the data we need from the request context
                data = {
                    'text': request.form.get('text'),
                    'language': request.form.get('language'),
                    'gender': request.form.get('gender'),
                    'alpha': float(request.form.get('alpha', 1.0))
                }
                
                # Validate input
                if not all([data['text'], data['language'], data['gender']]):
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }), 400
                
                # Limit text length more aggressively for Render deployment
                if len(data['text']) > 300:  # Reduced from 500 to 300 for Render
                    return jsonify({
                        'status': 'error',
                        'message': 'Text length exceeds maximum limit of 300 characters for free tier'
                    }), 400
                
                # Generate output filename with timestamp
                timestamp = int(time.time())
                filename = f'output_{data["language"]}_{data["gender"]}_{timestamp}.wav'
                output_file = os.path.join(os.path.abspath(app.config['UPLOAD_FOLDER']), filename)
                
                # Clean up old files
                cleanup_old_files(app.config['UPLOAD_FOLDER'])
                
                # Get the inference directory path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                inference_dir = os.path.join(current_dir, 'Fastspeech2_HS')
                
                # Submit the task to the thread pool with a shorter timeout
                future = executor.submit(
                    process_tts,
                    data['text'],
                    data['language'],
                    data['gender'],
                    data['alpha'],
                    output_file,
                    inference_dir
                )
                
                try:
                    # Wait for the result with a timeout
                    success = future.result(timeout=120)  # Increased to match other timeouts
                    
                    if success:
                        response = jsonify({
                            'status': 'success',
                            'audio_path': f'/static/audio/{filename}'
                        })
                        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                        response.headers['Pragma'] = 'no-cache'
                        response.headers['Expires'] = '0'
                        return response
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': 'TTS generation failed'
                        }), 500
                        
                except FuturesTimeoutError:
                    logger.error("Request timed out")
                    return jsonify({
                        'status': 'error',
                        'message': 'Request timed out. Please try with shorter text or try again.'
                    }), 504
                    
            except Exception as e:
                logger.error(f"Error in request processing: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            finally:
                gc.collect()
        return wrapper
    return decorator

# --- Routes ---

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/')
def home():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
        data = {
            'text': request.form.get('text'),
            'language': request.form.get('language'),
            'gender': request.form.get('gender'),
            'alpha': float(request.form.get('alpha', 1.0))
        }
        
        if not all([data['text'], data['language'], data['gender']]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
        
        # Increased text length limit for Standard plan
        if len(data['text']) > 1000:
            return jsonify({
                'status': 'error',
                'message': 'Text length exceeds maximum limit of 1000 characters'
            }), 400

        # Generate output filename with timestamp
        timestamp = int(time.time())
        filename = f"output_{data['language']}_{data['gender']}_{timestamp}.wav"
        output_file = os.path.join(os.path.abspath(app.config['UPLOAD_FOLDER']), filename)

        # Clean up old files
        cleanup_old_files(app.config['UPLOAD_FOLDER'])

        # Get the inference directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        inference_dir = os.path.join(current_dir, 'Fastspeech2_HS')

        # Submit the TTS processing to the executor
        future = executor.submit(
            process_tts,
            data['text'],
            data['language'],
            data['gender'],
            data['alpha'],
            output_file,
            inference_dir
        )

        try:
            # Wait for the result with a timeout
            success = future.result(timeout=120)  # Increased timeout to match process_tts

            if success:
                response = jsonify({
                    'status': 'success',
                    'audio_path': f'/static/audio/{filename}'
                })
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'TTS generation failed'
                }), 500
                
        except FuturesTimeoutError:
            logger.error("Request timed out")
            return jsonify({
                'status': 'error',
                'message': 'Request timed out. Please try with shorter text or try again.'
            }), 504
            
    except Exception as e:
        logger.error(f"Error in synthesize: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        gc.collect()

def cleanup_old_files(directory, max_age=7200):  # Increased to 2 hours
    try:
        current_time = time.time()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age:
                    os.remove(filepath)
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")

# --- Startup Logging ---
logger.info("Starting Flask application...")

# Ensure required directories exist
for directory in ['static/audio', 'tmp']:
    os.makedirs(directory, exist_ok=True)
    logger.info(f"Ensured directory exists: {directory}")

logger.info("Checking for ML models...")
if os.path.exists('Fastspeech2_HS'):
    logger.info("Fastspeech2_HS directory found")
else:
    logger.warning("Fastspeech2_HS directory not found - models need to be uploaded")

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error for debugging
    logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    # Return a JSON response with error details
    return jsonify({
        'status': 'error',
        'message': 'Internal Server Error: ' + str(e)
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4005))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
