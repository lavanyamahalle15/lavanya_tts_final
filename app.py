from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/audio'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def check_model_exists(language, gender):
    """Check if the model file exists for the given language and gender."""
    model_path = os.path.join('Fastspeech2_HS', language, gender, 'model', 'model.pth')
    return os.path.exists(model_path)

def check_phone_dict_exists(language):
    """Check if the phone dictionary exists for the given language."""
    dict_path = os.path.join('Fastspeech2_HS', 'phone_dict', language)
    return os.path.exists(dict_path) and os.path.getsize(dict_path) > 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
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
            }), 500
            
        if not check_phone_dict_exists(language):
            return jsonify({
                'status': 'error',
                'message': f'Phone dictionary for {language} is not available.'
            }), 500
        
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
        # Return error response with command output
        return jsonify({
            'status': 'error',
            'message': f'TTS generation failed: {e.stderr}'
        }), 500
    except Exception as e:
        # Return error response
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4005))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)