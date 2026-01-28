from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
import glob

generation_bp = Blueprint('generation', __name__)

@generation_bp.route('/generate', methods=['POST'])
def generate():
    if 'source_image' not in request.files or 'driven_audio' not in request.files:
        return jsonify({'success': False, 'error': 'Missing files'})

    source_image = request.files['source_image']
    driven_audio = request.files['driven_audio']

    if source_image.filename == '' or driven_audio.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    # Check for CPU flag
    use_cpu = request.form.get('use_cpu') == 'true'

    # Save files
    image_filename = secure_filename(source_image.filename)
    audio_filename = secure_filename(driven_audio.filename)
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    image_path = os.path.join(upload_folder, image_filename)
    audio_path = os.path.join(upload_folder, audio_filename)
    
    source_image.save(image_path)
    driven_audio.save(audio_path)

    # CALL SADTALKER INFERENCE
    sadtalker_dir = os.path.join(os.getcwd(), 'SadTalker')
    result_dir_abs = os.path.abspath(current_app.config['RESULT_FOLDER'])
    
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
    
    if use_cpu:
        command.append('--cpu')
        print("Force CPU mode enabled.")
    
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
