from flask import Blueprint, request, jsonify, current_app, url_for
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


@generation_bp.route('/api/generate-video', methods=['POST'])
def api_generate_video():
    """
    API endpoint for SadTalker video generation
    
    Form data:
        - image: Image file (portrait photo)
        - audio: Audio file
        - notes: Optional notes
    
    Returns:
        JSON with success status, video_url, or error message
    """
    try:
        # Validate files
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        image_file = request.files['image']
        audio_file = request.files['audio']
        
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400
        
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'No audio selected'}), 400
        
        # Secure filenames
        image_filename = secure_filename(image_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        
        # Save uploaded files
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        image_path = os.path.join(upload_folder, image_filename)
        audio_path = os.path.join(upload_folder, audio_filename)
        
        image_file.save(image_path)
        audio_file.save(audio_path)
        
        # Generate video using SadTalker
        generator = VideoGenerationService(current_app.root_path)
        result = generator.generate_video(
            image_path,
            audio_path,
            current_app.config['RESULT_FOLDER'],
            use_cpu=False  # Use GPU by default
        )
        
        if result.get('success'):
            # Convert file path to URL
            video_path = result.get('video_path', '')
            if video_path:
                # Get relative path from static folder
                static_path = os.path.relpath(video_path, current_app.static_folder)
                # Convert Windows backslashes to forward slashes for URL
                static_path_url = static_path.replace('\\', '/')
                video_url = url_for('static', filename=static_path_url, _external=True)
                result['video_url'] = video_url
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@generation_bp.route('/api/generate-tts', methods=['POST'])
def api_generate_tts():
    """
    API endpoint for VieNeu-TTS voice synthesis
    
    Form data:
        - text: Text to synthesize
        - model: Model repository (optional, default: pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf)
        - voice: Voice ID (default, Tuyen, Ngoc, etc., or 'clone')
        - ref_audio: Reference audio file (for voice cloning)
        - ref_text: Reference text transcript (for voice cloning)
    
    Returns:
        JSON with success status, audio_url, or error message
    """
    try:
        # Import VieNeu-TTS
        import sys
        vieneu_path = os.path.join(current_app.root_path, 'VieNeu-TTS')
        if vieneu_path not in sys.path:
            sys.path.insert(0, vieneu_path)
        
        from vieneu import Vieneu
        
        # Get parameters
        text = request.form.get('text', '').strip()
        voice_id = request.form.get('voice', 'default')
        model_repo = request.form.get('model', 'pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Log model selection for debugging
        print(f"[TTS] Model: {model_repo}, Voice: {voice_id}, Text length: {len(text)}")
        
        # Initialize TTS with selected model
        tts = Vieneu(backbone_repo=model_repo)
        
        # Generate audio based on voice selection
        if voice_id == 'clone':
            # Voice cloning mode
            if 'ref_audio' not in request.files:
                return jsonify({'success': False, 'error': 'No reference audio provided for cloning'}), 400
            
            ref_text = request.form.get('ref_text', '').strip()
            if not ref_text:
                return jsonify({'success': False, 'error': 'No reference text provided for cloning'}), 400
            
            ref_audio_file = request.files['ref_audio']
            if ref_audio_file.filename == '':
                return jsonify({'success': False, 'error': 'No reference audio selected'}), 400
            
            # Save reference audio
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            ref_audio_filename = secure_filename(ref_audio_file.filename)
            ref_audio_path = os.path.join(upload_folder, ref_audio_filename)
            ref_audio_file.save(ref_audio_path)
            
            # Generate with voice cloning
            audio_spec = tts.infer(
                text=text,
                ref_audio=ref_audio_path,
                ref_text=ref_text
            )
            
        elif voice_id != 'default':
            # Use preset voice
            try:
                voice_data = tts.get_preset_voice(voice_id)
                audio_spec = tts.infer(text=text, voice=voice_data)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Voice "{voice_id}" not found: {str(e)}'
                }), 400
        else:
            # Use default voice
            audio_spec = tts.infer(text=text)
        
        # Save generated audio
        result_folder = current_app.config['RESULT_FOLDER']
        os.makedirs(result_folder, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f'tts_{timestamp}.wav'
        audio_path = os.path.join(result_folder, audio_filename)
        
        tts.save(audio_spec, audio_path)
        
        # Convert to URL
        static_path = os.path.relpath(audio_path, current_app.static_folder)
        # Convert Windows backslashes to forward slashes for URL
        static_path_url = static_path.replace('\\', '/')
        audio_url = url_for('static', filename=static_path_url, _external=True)
        
        return jsonify({
            'success': True,
            'audio_url': audio_url,
            'audio_path': audio_path,
            'voice_used': voice_id,
            'text_length': len(text)
        })
        
    except ImportError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'VieNeu-TTS not available: {str(e)}'
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
