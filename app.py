from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
import requests
import json
import ssl
import logging
import sys
import base64
import io
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/audio'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def check_fastspeech_dir():
    """Check if Fastspeech2_HS directory exists"""
    return os.path.exists('Fastspeech2_HS')

def check_model_exists(language, gender):
    """Check if the model file exists for the given language and gender."""
    if not check_fastspeech_dir():
        logger.error("Fastspeech2_HS directory not found")
        return False
    model_path = os.path.join('Fastspeech2_HS', language, gender, 'model', 'model.pth')
    exists = os.path.exists(model_path)
    if not exists:
        logger.error(f"Model not found at {model_path}")
    return exists

def check_phone_dict_exists(language):
    """Check if the phone dictionary exists for the given language."""
    if not check_fastspeech_dir():
        logger.error("Fastspeech2_HS directory not found")
        return False
    dict_path = os.path.join('Fastspeech2_HS', 'phone_dict', language)
    exists = os.path.exists(dict_path) and os.path.getsize(dict_path) > 0
    if not exists:
        logger.error(f"Phone dictionary not found at {dict_path}")
    return exists

@app.route('/')
def health_check():
    """Health check endpoint that doesn't depend on ML models"""
    return jsonify({
        "status": "healthy",
        "models_available": check_fastspeech_dir()
    }), 200

@app.route('/status')
def status():
    """Detailed status endpoint"""
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
        # First check if Fastspeech2_HS exists
        if not check_fastspeech_dir():
            return jsonify({
                'status': 'error',
                'message': 'TTS models are not available. Please ensure Fastspeech2_HS directory is present.'
            }), 503

        # Get form data
        text = request.form['text']
        language = request.form['language']
        gender = request.form['gender']
        alpha = float(request.form.get('alpha', 1.0))
        
        # Check if model and dictionary exist
        if not check_model_exists(language, gender):
            return jsonify({
                'status': 'error',
                'message': f'TTS model for {language} ({gender}) is not available.'
            }), 503
            
        if not check_phone_dict_exists(language):
            return jsonify({
                'status': 'error',
                'message': f'Phone dictionary for {language} is not available.'
            }), 503
        
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
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Inference failed: {process.stderr}")
            return jsonify({
                'status': 'error',
                'message': f'TTS generation failed: {process.stderr}'
            }), 500
        
        # Return success response
        return jsonify({
            'status': 'success',
            'audio_path': f'/static/audio/{filename}'
        })
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error: {e.stderr}")
        return jsonify({
            'status': 'error',
            'message': f'TTS generation failed: {e.stderr}'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Log startup
logger.info("Starting Flask application...")
logger.info("Checking for ML models...")
if check_fastspeech_dir():
    logger.info("Fastspeech2_HS directory found")
else:
    logger.warning("Fastspeech2_HS directory not found - models need to be uploaded")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4005))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)