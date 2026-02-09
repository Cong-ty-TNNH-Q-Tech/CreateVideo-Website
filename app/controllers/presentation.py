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

print("DEBUG: Importing PresentationVideoExporter", flush=True)

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
        # Try to get data from potential JSON body safely (silent=True returns None if not JSON)
        data = request.get_json(silent=True)
        
        if data:
            # Handle JSON request
            text = data.get('text', 'Xin chào, đây là giọng nói mẫu.')
            voice_id = data.get('voice_id')
            clone_file = None
            clone_voice_path = data.get('clone_voice_path')
        else:
            # Handle Form Data (multipart/form-data)
            text = request.form.get('text', 'Xin chào, đây là giọng nói mẫu.')
            voice_id = request.form.get('voice_id')
            clone_file = request.files.get('clone_file')
            clone_voice_path = None # Will be set later if clone_file exists

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
        
        if clone_file:
            # Save uploaded clone file temporarily
            clone_filename = f"clone_source_{uuid.uuid4().hex}.wav"
            clone_voice_path = os.path.join(temp_dir, clone_filename)
            clone_file.save(clone_voice_path)
            # If both clone_file and clone_voice_path (from JSON) were somehow present (unlikely), 
            # the file upload takes precedence here.
        
        # clone_voice_path is already set from data if JSON was used

        
        # Generate audio (voice_type not used in preview, always auto-detect)
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
        voice_type = data.get('voice_type')  # 'vieneu', 'gtts', or 'clone'
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
                    voice_type=voice_type,
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
        voice_type = data.get('voice_type')
        voice_id = data.get('voice_id')
        clone_voice_path = data.get('clone_voice_path')
        
        # Generate audio file path
        audio_file_path = audio_service.get_audio_file_path(pres_id, slide_num, static_folder)
        audio_url = audio_service.get_audio_url(pres_id, slide_num)
        
        # Generate audio with optional voice settings
        success, message = audio_service.generate_audio(
            text_to_convert, 
            audio_file_path,
            voice_type=voice_type,
            voice_id=voice_id,
            clone_voice_path=clone_voice_path
        )
        
        if success:
            # Update slide with audio URL
            current_app.presentation_model.update_slide(pres_id, slide_num, {
                'audio_url': audio_url,
                'audio_file_path': audio_file_path,
                'video_url': None, # Reset video if audio changes
                'video_path': None
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

@presentation_bp.route('/presentation/<pres_id>/slide/<int:slide_num>/generate_slide_video', methods=['POST'])
def generate_slide_video(pres_id, slide_num):
    """Generate video for a single slide (slide image + audio)"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
        
        slide = current_app.presentation_model.get_slide(pres_id, slide_num)
        if not slide:
            return jsonify({'success': False, 'error': 'Slide not found'}), 404
        
        # Check if audio exists
        audio_path = slide.get('audio_file_path')
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({
                'success': False,
                'error': 'Audio not found. Please generate audio first.'
            }), 400
        
        # Extract slide image
        pres_file_path = presentation.get('file_path')
        if not pres_file_path or not os.path.exists(pres_file_path):
            return jsonify({
                'success': False,
                'error': 'Presentation file not found'
            }), 400
        
        pres_upload_dir = os.path.dirname(pres_file_path)
        slides_image_dir = os.path.join(pres_upload_dir, 'slides')
        
        # Extract slide images if not exists
        slide_image_path = os.path.join(slides_image_dir, f'slide_{slide_num}.png')
        if not os.path.exists(slide_image_path):
            print(f"📄 Extracting slide images from: {pres_file_path}")
            try:
                PresentationReader.extract_slide_images(pres_file_path, slides_image_dir)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to extract slide image: {str(e)}'
                }), 500
        
        if not os.path.exists(slide_image_path):
            return jsonify({
                'success': False,
                'error': f'Slide image not found: slide_{slide_num}.png'
            }), 400
        
        # Create single-slide video
        static_folder = current_app.static_folder
        video_dir = os.path.join(static_folder, 'videos', pres_id, 'slides')
        os.makedirs(video_dir, exist_ok=True)
        
        output_filename = f'slide_{slide_num}.mp4'
        output_path = os.path.join(video_dir, output_filename)
        
        print(f"🎬 Generating video for slide {slide_num}...")
        print(f"  Image: {slide_image_path}")
        print(f"  Audio: {audio_path}")
        print(f"  Output: {output_path}")
        
        # Use PresentationVideoExporter for single slide
        exporter = PresentationVideoExporter()
        slides_data = [{
            'image_path': slide_image_path,
            'audio_path': audio_path
        }]
        
        result = exporter.create_presentation_video(slides_data, output_path)
        
        if result['success']:
            video_url = f'/static/videos/{pres_id}/slides/{output_filename}'
            
            # Update slide with video info
            current_app.presentation_model.update_slide(pres_id, slide_num, {
                'slide_video_url': video_url,
                'slide_video_path': output_path
            })
            
            print(f"✅ Video for slide {slide_num} created: {video_url}")
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'message': f'Video for slide {slide_num} created successfully!'
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Video generation failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        print(f"❌ Error generating slide video: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Lỗi không mong đợi: {str(e)}'
        }), 500

@presentation_bp.route('/presentation/<pres_id>/merge_slide_videos', methods=['POST'])
def merge_slide_videos(pres_id):
    """Merge all individual slide videos into final presentation"""
    try:
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404
        
        slides = presentation.get('slides', [])
        
        # Collect slide video paths in order
        video_paths = []
        missing_slides = []
        
        for slide in slides:
            slide_num = slide.get('slide_num')
            video_path = slide.get('slide_video_path')
            
            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
            else:
                missing_slides.append(slide_num)
        
        if not video_paths:
            return jsonify({
                'success': False,
                'error': 'No slide videos found. Please generate videos for slides first.'
            }), 400
        
        print(f"🎬 Merging {len(video_paths)} slide videos...")
        if missing_slides:
            print(f"⚠️ Skipping {len(missing_slides)} slides without videos: {missing_slides}")
        
        # Output path
        static_folder = current_app.static_folder
        video_dir = os.path.join(static_folder, 'videos', pres_id)
        os.makedirs(video_dir, exist_ok=True)
        
        output_filename = f'final_presentation_{uuid.uuid4().hex}.mp4'
        output_path = os.path.join(video_dir, output_filename)
        
        # Merge videos using moviepy
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        clips = []
        try:
            for path in video_paths:
                clip = VideoFileClip(path)
                clips.append(clip)
            
            final_video = concatenate_videoclips(clips, method="compose")
            
            print(f"📹 Writing merged video to: {output_path}")
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                threads=4,
                logger=None
            )
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            video_url = f'/static/videos/{pres_id}/{output_filename}'
            
            # Update presentation
            current_app.presentation_model.update(pres_id, {
                'final_video_url': video_url,
                'final_video_path': output_path
            })
            
            print(f"✅ Merged video created: {video_url}")
            
            message = f'Merged {len(video_paths)} slide videos successfully!'
            if missing_slides:
                message += f' (Skipped {len(missing_slides)} slides without videos)'
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'message': message,
                'slides_merged': len(video_paths),
                'slides_skipped': len(missing_slides)
            })
            
        except Exception as e:
            # Clean up clips on error
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            raise e
        
    except Exception as e:
        print(f"❌ Error merging videos: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Lỗi không mong đợi: {str(e)}'
        }), 500



@presentation_bp.route('/presentation/<pres_id>/generate_final_video_v2', methods=['POST'])
def generate_final_video_v2(pres_id):
    """
    Unified endpoint for Step 4: Generate Final Video
    Can optionally include Talking Head overlay
    """
    try:
        data = request.form
        use_talking_head = data.get('use_talking_head') == 'true'
        
        print(f"🎬 Generating Final Video V2 for {pres_id}")
        print(f"   Use Talking Head: {use_talking_head}")
        
        presentation = current_app.presentation_model.get_by_id(pres_id)
        if not presentation:
            return jsonify({'success': False, 'error': 'Presentation not found'}), 404

        # 1. Merge Slide Videos (Base Video)
        # We reuse the logic from merge_slide_videos but internal
        # First check if slides have videos
        slides = presentation.get('slides', [])
        video_paths = []
        for slide in slides:
            v_path = slide.get('slide_video_path')
            if v_path and os.path.exists(v_path):
                video_paths.append(v_path)
        
        if not video_paths:
            return jsonify({
                'success': False,
                'error': 'Chưa có video slide nào. Vui lòng tạo video cho từng slide ở Bước 3 trước.'
            }), 400

        # Create base video
        static_folder = current_app.static_folder
        video_dir = os.path.join(static_folder, 'videos', pres_id)
        os.makedirs(video_dir, exist_ok=True)
        
        base_filename = f'base_presentation_{uuid.uuid4().hex}.mp4'
        base_output_path = os.path.join(video_dir, base_filename)
        
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        clips = []
        try:
            for path in video_paths:
                clips.append(VideoFileClip(path))
            
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(
                base_output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                threads=4,
                logger=None
            )
            final_video.close()
            for clip in clips: clip.close()
            
        except Exception as e:
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Lỗi khi ghép video slides: {str(e)}'}), 500

        # If NO Talking Head, we are done
        if not use_talking_head:
            video_url = f'/static/videos/{pres_id}/{base_filename}'
            current_app.presentation_model.update(pres_id, {
                'final_video_url': video_url,
                'final_video_path': base_output_path
            })
            return jsonify({
                'success': True,
                'video_url': video_url,
                'message': 'Đã tạo video thành công (Không có MC ảo)!'
            })

        # 2. Process Talking Head (If Enabled)
        # Check avatar
        if 'avatar' not in request.files:
             return jsonify({'success': False, 'error': 'Vui lòng chọn ảnh Avatar cho MC ảo'}), 400
             
        avatar_file = request.files['avatar']
        if avatar_file.filename == '':
             return jsonify({'success': False, 'error': 'Chưa chọn file Avatar'}), 400
             
        # Save avatar
        avatar_dir = os.path.join(static_folder, 'avatars', pres_id)
        os.makedirs(avatar_dir, exist_ok=True)
        avatar_filename = secure_filename(avatar_file.filename)
        avatar_path = os.path.join(avatar_dir, avatar_filename)
        avatar_file.save(avatar_path)
        
        # Check full audio
        full_audio_path = presentation.get('full_audio_path')
        if not full_audio_path or not os.path.exists(full_audio_path):
             # Try to generate full audio on the fly if missing? 
             # Or ask user to go back to step 3?
             # For now, require step 3 full audio.
             # Actually, we can just concatenate slide audios here if needed.
             # But let's assume user did "Generate Audio" in Step 3 which should usually persist.
             # Wait, "Generate Audio" in Step 3 generates per slide. "Merge Audio" is typically implicit or separate.
             # Let's check if we can merge strictly from slide audios here to be safe.
             
             # Attempt to merge audio on the fly
             audio_service = get_audio_service()
             audio_paths = []
             for i, slide in enumerate(slides):
                 a_path = slide.get('audio_file_path')
                 if a_path and os.path.exists(a_path):
                     audio_paths.append(a_path)
             
             if not audio_paths:
                 return jsonify({'success': False, 'error': 'Chưa có audio. Vui lòng tạo audio ở Bước 3.'}), 400
                 
             full_audio_filename = f"full_audio_temp_{uuid.uuid4().hex}.mp3"
             full_audio_path = os.path.join(static_folder, 'audio', pres_id, full_audio_filename)
             os.makedirs(os.path.dirname(full_audio_path), exist_ok=True)
             
             if not audio_service.merge_audio_files(audio_paths, full_audio_path):
                 return jsonify({'success': False, 'error': 'Lỗi khi gộp file audio.'}), 500

        # Generate Talking Head Video
        print("🤖 Generating Talking Head Video...")
        app_root = current_app.root_path
        video_service = VideoGenerationService(app_root)
        
        th_result_dir = os.path.join(static_folder, 'videos', pres_id, 'talking_head_temp')
        os.makedirs(th_result_dir, exist_ok=True)
        
        th_result = video_service.generate_video(
            source_image_path=avatar_path,
            driven_audio_path=full_audio_path,
            result_dir=th_result_dir,
            use_cpu=False
        )
        
        if not th_result['success']:
            return jsonify({'success': False, 'error': th_result.get('error', 'Lỗi tạo MC ảo')}), 500
            
        talking_head_video_path = th_result['video_path']
        
        # 3. Overlay Talking Head
        print("✨ Overlaying Talking Head...")
        final_filename = f'final_with_avatar_{uuid.uuid4().hex}.mp4'
        final_output_path = os.path.join(video_dir, final_filename)
        
        exporter = PresentationVideoExporter()
        overlay_result = exporter.overlay_talking_head(
            base_output_path, 
            talking_head_video_path, 
            final_output_path
        )
        
        if overlay_result['success']:
            video_url = f'/static/videos/{pres_id}/{final_filename}'
            current_app.presentation_model.update(pres_id, {
                'final_video_url': video_url,
                'final_video_path': final_output_path
            })
            return jsonify({
                'success': True, 
                'video_url': video_url,
                'message': 'Đã tạo video thành công (Kèm MC ảo)!'
            })
        else:
             return jsonify({'success': False, 'error': f"Lỗi khi ghép MC ảo: {overlay_result.get('error')}"}), 500

    except Exception as e:
        print(f"❌ Error in generate_final_video_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"Lỗi hệ thống: {str(e)}"}), 500
