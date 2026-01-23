from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload and result folders
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'source_image' not in request.files or 'driven_audio' not in request.files:
        return jsonify({'success': False, 'error': 'Missing files'})

    source_image = request.files['source_image']
    driven_audio = request.files['driven_audio']

    if source_image.filename == '' or driven_audio.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    # Save files
    image_filename = secure_filename(source_image.filename)
    audio_filename = secure_filename(driven_audio.filename)
    
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    
    source_image.save(image_path)
    driven_audio.save(audio_path)

    # CALL SADTALKER INFERENCE
    import subprocess
    import sys
    import glob

    sadtalker_dir = os.path.join(os.getcwd(), 'SadTalker')
    result_dir_abs = os.path.abspath(app.config['RESULT_FOLDER'])
    
    # Use venv python explicitly if possible to avoid environment mismatch
    venv_python = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_python):
        python_exec = venv_python
    else:
        python_exec = sys.executable

    # Construct command
    # python inference.py --driven_audio <audio> --source_image <image> --result_dir <dir> --still --preprocess full
    command = [
        python_exec, 'inference.py',
        '--driven_audio', os.path.abspath(audio_path),
        '--source_image', os.path.abspath(image_path),
        '--result_dir', result_dir_abs,
        '--still', 
        '--preprocess', 'resize',  # Changed from 'full' to 'resize' to save memory
        '--checkpoint_dir', 'checkpoints',
        '--batch_size', '1' # Force batch size 1
    ]
    
    
    
    print(f"Running command: {' '.join(command)}")

    try:
        # Run inference
        process = subprocess.run(
            command, 
            cwd=sadtalker_dir, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            print(f"Error Output: {process.stderr}")
            return jsonify({'success': False, 'error': f"SadTalker Error: {process.stderr}"})
            
        print(f"Output: {process.stdout}")

        # Find the latest generated MP4 file in the result directory
        list_of_files = glob.glob(os.path.join(result_dir_abs, '*.mp4'))
        if not list_of_files:
             return jsonify({'success': False, 'error': "No video generated."})
             
        latest_file = max(list_of_files, key=os.path.getctime)
        result_filename = os.path.basename(latest_file)
        
        return jsonify({
            'success': True,
            'video_url': f'/static/results/{result_filename}'
        })

    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
