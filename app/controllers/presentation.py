from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import traceback
from app.utils.presentation_reader import PresentationReader
from app.services.gemini import get_gemini_service
from app.services.audio_service import get_audio_service
from app.services.video_generator import VideoGenerationService
from app.services.presentation_video_exporter import PresentationVideoExporter

presentation_bp = Blueprint('presentation', __name__, url_prefix='/api')

# Allowed file extensions for avatar upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@presentation_bp.route('/upload-presentation', methods=['POST'])
def upload_presentation():
    """Upload PPT/PDF file and parse content"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file type
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pptx', '.ppt', '.pdf']:
        return jsonify({'success': False, 'error': 'Invalid file type. Only .pptx, .ppt, .pdf are allowed'}), 400
    
    try:
        # Generate unique ID for presentation
        pres_id = str(uuid.uuid4())
        pres_dir = os.path.join(current_app.config['PRESENTATION_FOLDER'], pres_id)
        os.makedirs(pres_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(pres_dir, filename)
        file.save(file_path)
        
        # Read presentation content
        reader = PresentationReader()
        slides = reader.extract_text_from_file(file_path)
        
        if not slides:
            return jsonify({'success': False, 'error': 'No content found in file'}), 400
        
        # Add to model
        presentation_data = current_app.presentation_model.add(filename, file_path, ext, slides, pres_id=pres_id)
        
        return jsonify({
            'success': True,
            'presentation_id': pres_id,
            'filename': filename,
            'total_slides': len(slides),
            'slides': slides
        })
        
    except Exception as e:
        print(f"Error uploading presentation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>', methods=['GET'])
def get_presentation(pres_id):
    """Get presentation info"""
    presentation = current_app.presentation_model.get_by_id(pres_id)
    if not presentation:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    return jsonify({
        'success': True,
        'presentation': presentation
    })

@presentation_bp.route('/presentation/<pres_id>/slides', methods=['GET'])
def get_slides(pres_id):
    """Get all slides"""
    print(f"DEBUG: get_slides called for {pres_id}", flush=True)
    presentation = current_app.presentation_model.get_by_id(pres_id)
    if not presentation:
        print(f"DEBUG: Presentation {pres_id} not found in model", flush=True)
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    return jsonify({
        'success': True,
        'slides': presentation['slides'],
        'full_audio_url': presentation.get('full_audio_url')
    })

@presentation_bp.route('/presentation/<pres_id>/slide/<int:slide_num>', methods=['GET'])
def get_slide(pres_id, slide_num):
    """Get specific slide info"""
    slide = current_app.presentation_model.get_slide(pres_id, slide_num)
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    return jsonify({
        'success': True,
        'slide': slide
    })

# ==================== GEMINI ROUTES ====================

@presentation_bp.route('/generate-text', methods=['POST'])
def generate_text():
    """Generate text with Gemini from slide content"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    language = data.get('language', 'vi')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    slide = current_app.presentation_model.get_slide(pres_id, slide_num)
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    try:
        gemini = get_gemini_service()
        if gemini is None:
            return jsonify({
                'success': False, 
                'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'
            }), 500
        
        # Generate text using the new method for TTS scripts
        generated_text = gemini.generate_script(slide['content'], language=language)
        
        # Update slide
        current_app.presentation_model.update_slide(pres_id, slide_num, {
            'generated_text': generated_text,
            'edited_text': generated_text if not slide.get('edited_text') else slide.get('edited_text')
        })
        
        return jsonify({
            'success': True,
            'text': generated_text,
            'slide_num': slide_num
        })
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/save-text', methods=['POST'])
def save_text():
    """Save user edited text"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    edited_text = data.get('edited_text', '')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    if not current_app.presentation_model.update_slide(pres_id, slide_num, {'edited_text': edited_text}):
         return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    return jsonify({
        'success': True,
        'message': 'Text saved successfully'
    })

@presentation_bp.route('/save-all-texts', methods=['POST'])
def save_all_texts():
    """Save all edited texts"""
    data = request.json
    pres_id = data.get('presentation_id')
    slides_data = data.get('slides_data', []) # List of {slide_num: x, text: y}
    
    if not pres_id or not slides_data:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    success_count = 0
    for item in slides_data:
        slide_num = item.get('slide_num')
        text = item.get('text')
        if slide_num is not None:
             if current_app.presentation_model.update_slide(pres_id, slide_num, {'edited_text': text}):
                 success_count += 1
    
    return jsonify({
        'success': True,
        'saved_count': success_count,
        'message': f'Saved {success_count} scripts'
    })

@presentation_bp.route('/enhance-text', methods=['POST'])
def enhance_text():
    """Enhance text with Gemini"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    instruction = data.get('instruction', '')
    current_text = data.get('current_text', '')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    if not current_text:
        return jsonify({'success': False, 'error': 'Missing current_text'}), 400
    
    try:
        gemini = get_gemini_service()
        if gemini is None:
            return jsonify({
                'success': False, 
                'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'
            }), 500
        
        enhanced_text = gemini.enhance_text(current_text, instruction)
        
        return jsonify({
            'success': True,
            'enhanced_text': enhanced_text
        })
    except Exception as e:
        print(f"Error enhancing text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/regenerate-text', methods=['POST'])
def regenerate_text():
    """Regenerate text with feedback"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    feedback = data.get('feedback', '')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    slide = current_app.presentation_model.get_slide(pres_id, slide_num)
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
        
    try:
        gemini = get_gemini_service()
        if gemini is None:
            return jsonify({
                'success': False, 
                'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'
            }), 500
        
        current_val = slide.get('edited_text', slide.get('generated_text', ''))
        new_text = gemini.regenerate_text(slide['content'], current_val, feedback)
        
        # Update slide
        current_app.presentation_model.update_slide(pres_id, slide_num, {
            'generated_text': new_text,
            'edited_text': new_text
        })
        
        return jsonify({
            'success': True,
            'text': new_text
        })
    except Exception as e:
        print(f"Error regenerating text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AUDIO ROUTES ====================

@presentation_bp.route('/available-voices', methods=['GET'])
def get_available_voices():
    """Get list of available VieNeu-TTS preset voices"""
    try:
        audio_service = get_audio_service()
        voices = audio_service.get_available_voices()
        
        return jsonify({
            'success': True,
            'voices': voices,
            'vieneu_available': audio_service.vieneu_available
        })
    except Exception as e:
        print(f"Error getting voices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/preview-voice', methods=['POST'])
def preview_voice():
    """Generate a short preview audio with selected voice"""
    try:
        # Check if content type is multipart/form-data (file upload) or json
        if request.content_type and 'multipart/form-data' in request.content_type:
            text = request.form.get('text', 'Xin chào, đây là giọng nói mẫu.')
            voice_id = request.form.get('voice_id')
            clone_file = request.files.get('clone_file')
        else:
            data = request.json or {}
            text = data.get('text', 'Xin chào, đây là giọng nói mẫu.')
            voice_id = data.get('voice_id')
            clone_file = None

        # Limit text length for preview
        if len(text) > 100:
            text = text[:100]
            
        audio_service = get_audio_service()
        static_folder = current_app.static_folder
        
        # Create temp folder if not exists
        temp_dir = os.path.join(static_folder, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"preview_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(temp_dir, filename)
        
        clone_voice_path = None
        if clone_file:
            # Save uploaded clone file temporarily
            clone_filename = f"clone_source_{uuid.uuid4().hex}.wav"
            clone_voice_path = os.path.join(temp_dir, clone_filename)
            clone_file.save(clone_voice_path)
        elif request.json:
             # Handle clone path if passed directly (less likely for preview but good for API)
             clone_voice_path = request.json.get('clone_voice_path')

        
        # Generate audio
        success, message = audio_service.generate_audio(
            text, 
            output_path, 
            voice_id=voice_id, 
            clone_voice_path=clone_voice_path
        )
        
        # Clean up clone source file if it was uploaded
        if clone_file and clone_voice_path and os.path.exists(clone_voice_path):
             # Optional: keep it or delete it? For preview maybe delete. 
             # But if VieNeu needs it during generation, it loads it.
             # VieNeu load_voice usually reads it. Safe to delete AFTER generation?
             # Let's keep it for now or delete if confident. 
             # Actually, if generation failed, we might want to debug.
             # But to save space, let's not delete immediately, or maybe simple cleanup job later.
             pass
        
        if success:
            # Return URL to the audio file
            audio_url = f"/static/temp/{filename}"
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        print(f"Error previewing voice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>/generate_audio', methods=['POST'])
def generate_audio(pres_id):
    """Generate audio files for all slides in a presentation"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
        
        # Get audio service
        audio_service = get_audio_service()
        
        # Get static folder for saving audio files
        static_folder = current_app.static_folder
        
        slides = presentation.get('slides', [])
        if not slides:
            return jsonify({'success': False, 'error': 'No slides found'}), 400
        
        
        # Get voice settings from request body (optional)
        try:
            data = request.get_json(silent=True) or {}
        except:
            data = {}
        voice_id = data.get('voice_id')
        clone_voice_path = data.get('clone_voice_path')
        
        results = []
        success_count = 0
        
        for i, slide in enumerate(slides):
            try:
                # Get the text to convert (edited_text takes priority over generated_text)
                text_to_convert = slide.get('edited_text') or slide.get('generated_text') or slide.get('content', '')
                
                if not text_to_convert.strip():
                    results.append({
                        'slide_index': i,
                        'success': False,
                        'message': 'No text available for this slide'
                    })
                    continue
                
                # Generate audio file path
                audio_file_path = audio_service.get_audio_file_path(pres_id, i, static_folder)
                audio_url = audio_service.get_audio_url(pres_id, i)
                
                # Generate audio
                success, message = audio_service.generate_audio(
                    text_to_convert, 
                    audio_file_path,
                    voice_id=voice_id,
                    clone_voice_path=clone_voice_path
                )
                
                if success:
                    # Update slide with audio URL
                    current_app.presentation_model.update_slide(pres_id, i, {
                        'audio_url': audio_url,
                        'audio_file_path': audio_file_path
                    })
                    success_count += 1
                    
                results.append({
                    'slide_index': i,
                    'success': success,
                    'audio_url': audio_url if success else None,
                    'message': message
                })
                
            except Exception as e:
                print(f"Error processing slide {i}: {str(e)}")
                results.append({
                    'slide_index': i,
                    'success': False,
                    'message': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_slides': len(slides),
            'success_count': success_count,
            'results': results
        })
        
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>/concatenate_audio', methods=['POST'])
def concatenate_audio(pres_id):
    """Merge all slide audios into one file"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
            
        slides = presentation.get('slides', [])
        if not slides:
             return jsonify({'success': False, 'error': 'No slides found'}), 400
             
        audio_service = get_audio_service()
        static_folder = current_app.static_folder
        
        # Collect audio paths from slides
        audio_paths = []
        for i, slide in enumerate(slides):
            # Prefer audio_file_path from slide data, or reconstruct it
            path = slide.get('audio_file_path')
            if not path or not os.path.exists(path):
                 # Try to reconstruct standard path
                 path = audio_service.get_audio_file_path(pres_id, i, static_folder)
            
            if os.path.exists(path):
                audio_paths.append(path)
        
        if not audio_paths:
            return jsonify({'success': False, 'error': 'No audio files found to merge'}), 400
            
        # Output path
        output_filename = f"full_presentation_{uuid.uuid4().hex}.mp3"
        output_dir = os.path.join(static_folder, 'audio', pres_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        # Merge
        if audio_service.merge_audio_files(audio_paths, output_path):
            audio_url = f"/static/audio/{pres_id}/{output_filename}"
            # Update presentation with full audio url
            current_app.presentation_model.update(pres_id, {
                'full_audio_url': audio_url,
                'full_audio_path': output_path
            })
            
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'message': 'Audio merged successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to merge audio files'}), 500
            
    except Exception as e:
        print(f"Error concatenating audio: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>/upload_avatar', methods=['POST'])
def upload_avatar(pres_id):
    """Upload avatar image for Step 4"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404

        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
            
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            static_folder = current_app.static_folder
            avatar_dir = os.path.join(static_folder, 'avatars', pres_id)
            os.makedirs(avatar_dir, exist_ok=True)
            
            filename = f"avatar_{uuid.uuid4().hex}.png" # Force png or keep original ext
            # Better to keep ext usually, but consistency helps.
            # Let's clean filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(avatar_dir, filename)
            file.save(file_path)
            
            avatar_url = f"/static/avatars/{pres_id}/{filename}"
            
            # Update presentation with avatar
            current_app.presentation_model.update(pres_id, {
                'avatar_url': avatar_url,
                'avatar_path': file_path
            })
            
            return jsonify({
                'success': True, 
                'avatar_url': avatar_url,
                'message': 'Avatar uploaded successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        print(f"Error uploading avatar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>/slide/<int:slide_num>/regenerate_audio', methods=['POST'])
def regenerate_audio(pres_id, slide_num):
    """Regenerate audio for a specific slide"""
    try:
        slide = current_app.presentation_model.get_slide(pres_id, slide_num)
        if not slide:
            return jsonify({'success': False, 'error': 'Slide not found'}), 404
        
        # Get audio service
        audio_service = get_audio_service()
        
        # Get static folder for saving audio files
        static_folder = current_app.static_folder
        
        # Get the text to convert (edited_text takes priority over generated_text)
        text_to_convert = slide.get('edited_text') or slide.get('generated_text') or slide.get('content', '')
        
        if not text_to_convert.strip():
            return jsonify({
                'success': False, 
                'error': 'No text available for this slide'
            }), 400
        
        
        # Get voice settings from request body (optional) - backward compatible
        try:
            data = request.get_json(silent=True) or {}
        except:
            data = {}
        voice_id = data.get('voice_id')
        clone_voice_path = data.get('clone_voice_path')
        
        # Generate audio file path
        audio_file_path = audio_service.get_audio_file_path(pres_id, slide_num, static_folder)
        audio_url = audio_service.get_audio_url(pres_id, slide_num)
        
        # Generate audio with optional voice settings
        success, message = audio_service.generate_audio(
            text_to_convert, 
            audio_file_path,
            voice_id=voice_id,
            clone_voice_path=clone_voice_path
        )
        
        if success:
            # Update slide with audio URL
            current_app.presentation_model.update_slide(pres_id, slide_num, {
                'audio_url': audio_url,
                'audio_file_path': audio_file_path
            })
            
            return jsonify({
                'success': True,
                'message': message,
                'audio_url': audio_url,
                'slide_num': slide_num
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to generate audio: {message}"
            }), 500
        
    except Exception as e:
        print(f"Error in regenerate_audio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@presentation_bp.route('/presentation/<pres_id>/generate_video', methods=['POST'])
def generate_video(pres_id):
    """Generate talking head video using SadTalker (Step 5)"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
        
        # Validate avatar exists
        avatar_path = presentation.get('avatar_path')
        if not avatar_path or not os.path.exists(avatar_path):
            return jsonify({
                'success': False,
                'error': 'Vui lòng upload avatar trước (Step 4)'
            }), 400
        
        # Validate merged audio exists
        full_audio_path = presentation.get('full_audio_path')
        if not full_audio_path or not os.path.exists(full_audio_path):
            return jsonify({
                'success': False,
                'error': 'Vui lòng tạo audio trước (Step 3). Cần merge tất cả audio slides.'
            }), 400
        
        # Initialize video generator
        # current_app.root_path points to 'app' folder
        # VideoGenerationService needs path to project root (parent of 'app')
        app_root = current_app.root_path  # This is the 'app' folder path
        video_service = VideoGenerationService(app_root)
        
        # Create result directory
        static_folder = current_app.static_folder
        result_dir = os.path.join(static_folder, 'videos', pres_id)
        os.makedirs(result_dir, exist_ok=True)
        
        print(f"🎬 Generating video with SadTalker...")
        print(f"  Avatar: {avatar_path}")
        print(f"  Audio: {full_audio_path}")
        print(f"  Result dir: {result_dir}")
        
        # Generate video
        result = video_service.generate_video(
            source_image_path=avatar_path,
            driven_audio_path=full_audio_path,
            result_dir=result_dir,
            use_cpu=False  # Use GPU if available
        )
        
        if result['success']:
            video_url = result['video_url']
            video_path = result['video_path']
            
            # Update presentation with video info
            current_app.presentation_model.update(pres_id, {
                'final_video_url': video_url,
                'final_video_path': video_path
            })
            
            print(f"✅ Video generated successfully: {video_url}")
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'message': 'Video tạo thành công!'
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Video generation failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        print(f"❌ Error generating video: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Lỗi không mong đợi: {str(e)}"
        }), 500

@presentation_bp.route('/presentation/<pres_id>/export_presentation_video', methods=['POST'])
def export_presentation_video(pres_id):
    """Export presentation as video (slides + audio) without SadTalker"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
        
        slides_data = presentation.get('slides', [])
        print(f"📊 Debug - Total slides in presentation: {len(slides_data)}")
        print(f"📊 Debug - Slides data: {slides_data}")
        
        if not slides_data or len(slides_data) == 0:
            return jsonify({
                'success': False,
                'error': 'No slides found in presentation'
            }), 400
        
        
        # Extract slide images from presentation file
        pres_file_path = presentation.get('file_path')
        if not pres_file_path or not os.path.exists(pres_file_path):
            return jsonify({
                'success': False,
                'error': 'Presentation file not found'
            }), 400
        
        # Create directory for extracted slides
        pres_upload_dir = os.path.dirname(pres_file_path)
        slides_image_dir = os.path.join(pres_upload_dir, 'slides')
        
        print(f"📄 Extracting slides from: {pres_file_path}")
        print(f"📁 Output directory: {slides_image_dir}")
        
        # Extract slides to images
        try:
            PresentationReader.extract_slide_images(pres_file_path, slides_image_dir)
        except NotImplementedError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to extract slides: {str(e)}'
            }), 500
        
        # Collect slides that have both image and audio
        slides_with_audio = []
        skipped_slides = []
        
        for slide in slides_data:
            slide_num = slide.get('slide_num', '?')
            audio_path = slide.get('audio_file_path')
            
            # Get extracted slide image path
            slide_image_path = os.path.join(slides_image_dir, f'slide_{slide_num}.png')
            
            print(f"🔍 Checking slide {slide_num}:")
            print(f"   Audio path: {audio_path}")
            print(f"   Audio exists: {os.path.exists(audio_path) if audio_path else 'No path'}")
            print(f"   Image path: {slide_image_path}")
            print(f"   Image exists: {os.path.exists(slide_image_path) if slide_image_path else 'No path'}")
            
            # Skip slides without audio or image
            if not audio_path or not os.path.exists(audio_path):
                print(f"⚠️ Skipping slide {slide_num}: no audio")
                skipped_slides.append(slide_num)
                continue
            
            if not os.path.exists(slide_image_path):
                print(f"⚠️ Skipping slide {slide_num}: no image")
                skipped_slides.append(slide_num)
                continue
            
            # Valid slide - add to list
            print(f"✅ Slide {slide_num} is valid!")
            slides_with_audio.append({
                'image_path': slide_image_path,
                'audio_path': audio_path
            })
        
        # Check if we have at least one valid slide
        if len(slides_with_audio) == 0:
            return jsonify({
                'success': False,
                'error': 'No slides with both image and audio found. Please generate audio for at least one slide.'
            }), 400

        
        # Create output directory
        static_folder = current_app.static_folder
        video_dir = os.path.join(static_folder, 'videos', pres_id)
        os.makedirs(video_dir, exist_ok=True)
        
        output_filename = f'presentation_{pres_id}.mp4'
        output_path = os.path.join(video_dir, output_filename)
        
        print(f"📹 Exporting presentation video...")
        print(f"  Slides: {len(slides_with_audio)}")
        print(f"  Output: {output_path}")
        
        # Create video
        exporter = PresentationVideoExporter()
        result = exporter.create_presentation_video(slides_with_audio, output_path)
        
        if result['success']:
            video_url = f'/static/videos/{pres_id}/{output_filename}'
            
            # Update presentation model
            current_app.presentation_model.update(pres_id, {
                'presentation_video_url': video_url,
                'presentation_video_path': output_path
            })
            
            print(f"✅ Presentation video exported: {video_url}")
            
            # Build success message
            message = f'Video tạo thành công với {len(slides_with_audio)} slide!'
            if skipped_slides:
                message += f' (Đã bỏ qua {len(skipped_slides)} slide thiếu audio/image)'
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'message': message,
                'slides_used': len(slides_with_audio),
                'slides_skipped': len(skipped_slides)
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Video export failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        print(f"❌ Error exporting presentation video: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Lỗi không mong đợi: {str(e)}"
        }), 500


