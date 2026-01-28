from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import time
import uuid
import json
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.presentation_reader import PresentationReader
from utils.gemini_service import GeminiService

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure upload and result folders
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
PRESENTATION_FOLDER = 'static/uploads/presentations'
DATA_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(PRESENTATION_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['PRESENTATION_FOLDER'] = PRESENTATION_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# In-memory storage for presentations (có thể thay bằng database)
presentations = {}

def load_presentations():
    """Load presentations từ file JSON"""
    global presentations
    json_path = os.path.join(DATA_FOLDER, 'presentations.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                presentations = json.load(f)
        except:
            presentations = {}

def save_presentations():
    """Save presentations vào file JSON"""
    json_path = os.path.join(DATA_FOLDER, 'presentations.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(presentations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving presentations: {e}")

# Load existing presentations on startup
load_presentations()

# Initialize Gemini service (lazy load - chỉ init khi cần)
gemini_service = None

def get_gemini_service():
    """Lazy load Gemini service"""
    global gemini_service
    if gemini_service is None:
        try:
            gemini_service = GeminiService()
        except Exception as e:
            print(f"Warning: Could not initialize Gemini service: {e}")
            print("Please set GEMINI_API_KEY environment variable")
    return gemini_service

@app.route('/')
def home():
    return render_template('presentation.html')

@app.route('/old')
def old_home():
    """Old SadTalker demo page"""
    return render_template('index.html')

# ==================== PRESENTATION ROUTES ====================

@app.route('/api/upload-presentation', methods=['POST'])
def upload_presentation():
    """Upload file PPT/PDF và đọc nội dung"""
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
        pres_dir = os.path.join(PRESENTATION_FOLDER, pres_id)
        os.makedirs(pres_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(pres_dir, filename)
        file.save(file_path)
        
        # Read presentation content
        reader = PresentationReader()
        slides = reader.extract_text_from_file(file_path)
        
        if not slides:
            return jsonify({'success': False, 'error': 'No content found in file'}), 400
        
        # Store presentation data
        presentation_data = {
            'id': pres_id,
            'filename': filename,
            'file_path': file_path,
            'type': ext,
            'slides': slides,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'avatar_path': None,
            'final_video_path': None
        }
        
        # Initialize slide data với empty fields
        for slide in presentation_data['slides']:
            slide['generated_text'] = ''
            slide['edited_text'] = ''
            slide['audio_path'] = None
            slide['video_path'] = None
            slide['status'] = 'pending'
        
        presentations[pres_id] = presentation_data
        save_presentations()
        
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

@app.route('/api/presentation/<pres_id>', methods=['GET'])
def get_presentation(pres_id):
    """Lấy thông tin presentation"""
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    return jsonify({
        'success': True,
        'presentation': presentations[pres_id]
    })

@app.route('/api/presentation/<pres_id>/slides', methods=['GET'])
def get_slides(pres_id):
    """Lấy danh sách tất cả slides"""
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    return jsonify({
        'success': True,
        'slides': presentations[pres_id]['slides']
    })

@app.route('/api/presentation/<pres_id>/slide/<int:slide_num>', methods=['GET'])
def get_slide(pres_id, slide_num):
    """Lấy thông tin slide cụ thể"""
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    slides = presentations[pres_id]['slides']
    slide = next((s for s in slides if s['slide_num'] == slide_num), None)
    
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    return jsonify({
        'success': True,
        'slide': slide
    })

# ==================== GEMINI API ROUTES ====================

@app.route('/api/generate-text', methods=['POST'])
def generate_text():
    """Generate text với Gemini từ slide content"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    language = data.get('language', 'vi')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    presentation = presentations[pres_id]
    slide = next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)
    
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    try:
        gemini = get_gemini_service()
        if gemini is None:
            return jsonify({
                'success': False, 
                'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'
            }), 500
        
        # Generate text từ slide content
        generated_text = gemini.generate_presentation_text(slide['content'], language=language)
        
        # Update slide
        slide['generated_text'] = generated_text
        if not slide.get('edited_text'):
            slide['edited_text'] = generated_text
        
        save_presentations()
        
        return jsonify({
            'success': True,
            'text': generated_text,
            'slide_num': slide_num
        })
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-text', methods=['POST'])
def save_text():
    """Lưu text đã chỉnh sửa của người dùng"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    edited_text = data.get('edited_text', '')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    presentation = presentations[pres_id]
    slide = next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)
    
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    # Update edited text
    slide['edited_text'] = edited_text
    save_presentations()
    
    return jsonify({
        'success': True,
        'message': 'Text saved successfully'
    })

@app.route('/api/enhance-text', methods=['POST'])
def enhance_text():
    """Cải thiện text với Gemini dựa trên instruction"""
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

@app.route('/api/regenerate-text', methods=['POST'])
def regenerate_text():
    """Tạo lại text với feedback từ user"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    feedback = data.get('feedback', '')
    
    if not pres_id or not slide_num:
        return jsonify({'success': False, 'error': 'Missing presentation_id or slide_num'}), 400
    
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    presentation = presentations[pres_id]
    slide = next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)
    
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    try:
        gemini = get_gemini_service()
        if gemini is None:
            return jsonify({
                'success': False, 
                'error': 'Gemini API not configured. Please set GEMINI_API_KEY environment variable.'
            }), 500
        
        current_text = slide.get('edited_text', slide.get('generated_text', ''))
        new_text = gemini.regenerate_text(slide['content'], current_text, feedback)
        
        # Update slide
        slide['generated_text'] = new_text
        slide['edited_text'] = new_text
        
        save_presentations()
        
        return jsonify({
            'success': True,
            'text': new_text
        })
    except Exception as e:
        print(f"Error regenerating text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
