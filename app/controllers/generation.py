from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.services.video_generator import VideoGenerationService

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

    # Use Service
    # app.root_path usually points to .../app
    generator = VideoGenerationService(current_app.root_path)
    result = generator.generate_video(
        image_path, 
        audio_path, 
        current_app.config['RESULT_FOLDER'],
        use_cpu=use_cpu
    )
    
    return jsonify(result)
