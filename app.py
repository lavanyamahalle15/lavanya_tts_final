from flask import Flask, render_template, request, send_file, jsonify, make_response
import os
import subprocess
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Helper functions ---

def check_fastspeech_dir():
    return os.path.exists('Fastspeech2_HS')

def check_model_exists(language, gender):
    """Check if the model file exists for the given language and gender."""
    model_path = os.path.join('Fastspeech2_HS', language, gender, 'model', 'model.pth')
    exists = os.path.exists(model_path)
    if not exists:
        logger.error(f"Model not found at {model_path}")
    return exists

def check_phone_dict_exists(language):
    """Check if the phone dictionary exists for the given language."""
    dict_path = os.path.join('Fastspeech2_HS', 'phone_dict', language)
    exists = os.path.exists(dict_path) and os.path.getsize(dict_path) > 0
    if not exists:
        logger.error(f"Phone dictionary not found at {dict_path}")
    return exists

# --- Routes ---

@app.route('/')
def home():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/status')
def status():
    if not check_fastspeech_dir():
        return jsonify({
            "status": "warning",
            "message": "Fastspeech2_HS directory not found. Models need to be uploaded.",
            "models_available": False
        }), 200
    
    return jsonify({
        "status": "ready",
        "models_available": True,
        "upload_dir": os.path.exists(app.config['UPLOAD_FOLDER'])
    }), 200

@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
        # Get form data
        text = request.form.get('text')
        language = request.form.get('language')
        gender = request.form.get('gender')
        alpha = float(request.form.get('alpha', 1.0))
        
        # Validate input
        if not all([text, language, gender]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
        
        # Check if model and dictionary exist
        if not check_model_exists(language, gender):
            return jsonify({
                'status': 'error',
                'message': f'TTS model for {language} ({gender}) is not available.'
            }, 404)
            
        if not check_phone_dict_exists(language):
            return jsonify({
                'status': 'error',
                'message': f'Phone dictionary for {language} is not available.'
            }, 404)
        
        # Generate output filename
        filename = f'output_{language}_{gender}.wav'
        output_file = os.path.join(os.path.abspath(app.config['UPLOAD_FOLDER']), filename)
        
        # Get the absolute path to inference.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        inference_dir = os.path.join(current_dir, 'Fastspeech2_HS')
        
        # Run inference.py with the provided parameters
        cmd = [
            'python',
            'inference.py',
            '--sample_text', text,
            '--language', language,
            '--gender', gender,
            '--alpha', str(alpha),
            '--output_file', output_file
        ]
        
        # Run the command from the Fastspeech2_HS directory
        process = subprocess.run(
            cmd,
            check=True,
            cwd=inference_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': f'TTS generation failed: {process.stderr}'
            }), 500
        
        # Check if file was generated
        if not os.path.exists(output_file):
            return jsonify({
                'status': 'error',
                'message': 'Audio file generation failed'
            }), 500
            
        # Return success response with cache control headers
        response = jsonify({
            'status': 'success',
            'audio_path': f'/static/audio/{filename}'
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'TTS generation timed out. Please try with shorter text.'
        }), 504
    except subprocess.CalledProcessError as e:
        return jsonify({
            'status': 'error',
            'message': f'TTS generation failed: {e.stderr}'
        }), 500
    except Exception as e:
        print(f"Error in synthesize: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# --- Startup Logging ---

logger.info("Starting Flask application...")
logger.info("Checking for ML models...")
if check_fastspeech_dir():
    logger.info("Fastspeech2_HS directory found")
else:
    logger.warning("Fastspeech2_HS directory not found - models need to be uploaded")
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error for debugging
    logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)

    # Return a JSON response with error details and status code 500
    response = {
        'status': 'error',
        'message': 'Internal Server Error: ' + str(e)
    }
    return jsonify(response), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4005))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
