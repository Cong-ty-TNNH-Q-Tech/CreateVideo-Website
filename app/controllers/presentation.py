from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from app.utils.presentation_reader import PresentationReader
from app.services.gemini import get_gemini_service

presentation_bp = Blueprint('presentation', __name__, url_prefix='/api')

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
        presentation_data = current_app.presentation_model.add(filename, file_path, ext, slides)
        
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
    presentation = current_app.presentation_model.get_by_id(pres_id)
    if not presentation:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    return jsonify({
        'success': True,
        'slides': presentation['slides']
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
        
        # Generate text
        generated_text = gemini.generate_presentation_text(slide['content'], language=language)
        
        # Update slide
        current_app.presentation_model.update_slide(pres_id, slide_num, {
            'generated_text': generated_text,
            'edited_text': generated_text if not slide.get('edited_text') else slide.get('edited_text') # Logic in original was: if not slide['edited_text'] then set it.
        })
        # Note: Original logic: if not slide.get('edited_text'): slide['edited_text'] = generated_text
        # My update above overwrites if not slide['edited_text'], wait.
        # Original:
        # slide['generated_text'] = generated_text
        # if not slide.get('edited_text'):
        #     slide['edited_text'] = generated_text
        
        # Let's verify my update_slide implementation logic. I passed a dict. 
        # So I should handle that properly.
        
        updates = {'generated_text': generated_text}
        if not slide.get('edited_text'):
             updates['edited_text'] = generated_text
        
        current_app.presentation_model.update_slide(pres_id, slide_num, updates)
        
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
