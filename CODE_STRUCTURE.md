# Cấu Trúc Code Mẫu

## 1. Updated requirements.txt

```txt
# Web Framework
Flask==3.0.0
huggingface_hub==0.19.0

# Presentation Reading
python-pptx==0.6.21
pypdf==3.17.0

# AI Services
google-generativeai==0.3.0

# Text-to-Speech
gtts==2.5.0
pydub==0.25.1

# Video Processing
moviepy==1.0.3
opencv-python==4.8.1.78
imageio==2.31.1
imageio-ffmpeg==0.4.9

# Image Processing
Pillow==10.0.0

# Utilities
python-dotenv==1.0.0
```

---

## 2. Cấu trúc thư mục mới

```
CreateVideo-Website/
├── app.py                          # Main Flask app
├── requirements.txt
├── .env                            # Environment variables
├── utils/
│   ├── __init__.py
│   ├── presentation_reader.py     # Đọc PPT/PDF
│   ├── gemini_service.py          # Gemini API
│   ├── tts_service.py             # Text-to-Speech
│   ├── video_generator.py         # SadTalker wrapper
│   └── video_composer.py          # Video composition
├── static/
│   ├── uploads/
│   │   ├── presentations/
│   │   └── avatars/
│   ├── audio/
│   └── results/
├── templates/
│   ├── index.html                 # Updated UI
│   └── presentation.html          # Multi-step form
└── data/
    └── presentations.json         # Metadata storage (optional)
```

---

## 3. Code Mẫu - utils/presentation_reader.py

```python
from pptx import Presentation
from pypdf import PdfReader
import os
from typing import List, Dict

class PresentationReader:
    """Đọc nội dung từ file PPT và PDF"""
    
    @staticmethod
    def read_pptx(file_path: str) -> List[Dict]:
        """
        Đọc file PowerPoint và trả về danh sách slides
        
        Returns:
            List[Dict]: [{
                'slide_num': int,
                'content': str,
                'notes': str (optional)
            }]
        """
        try:
            prs = Presentation(file_path)
            slides_data = []
            
            for idx, slide in enumerate(prs.slides, 1):
                content_parts = []
                
                # Đọc text từ shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        content_parts.append(shape.text.strip())
                
                # Đọc notes (nếu có)
                notes = ""
                if slide.has_notes_slide:
                    notes_slide = slide.notes_slide
                    if notes_slide.notes_text_frame:
                        notes = notes_slide.notes_text_frame.text
                
                content = "\n".join(content_parts)
                
                slides_data.append({
                    'slide_num': idx,
                    'content': content,
                    'notes': notes,
                    'total_slides': len(prs.slides)
                })
            
            return slides_data
        except Exception as e:
            raise Exception(f"Error reading PPTX: {str(e)}")
    
    @staticmethod
    def read_pdf(file_path: str) -> List[Dict]:
        """
        Đọc file PDF và trả về danh sách pages
        
        Returns:
            List[Dict]: [{
                'slide_num': int,
                'content': str
            }]
        """
        try:
            reader = PdfReader(file_path)
            pages_data = []
            
            for idx, page in enumerate(reader.pages, 1):
                content = page.extract_text()
                
                pages_data.append({
                    'slide_num': idx,
                    'content': content.strip(),
                    'total_slides': len(reader.pages)
                })
            
            return pages_data
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> List[Dict]:
        """Tự động detect loại file và đọc"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.pptx', '.ppt']:
            return PresentationReader.read_pptx(file_path)
        elif ext == '.pdf':
            return PresentationReader.read_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
```

---

## 4. Code Mẫu - utils/gemini_service.py

```python
import google.generativeai as genai
import os
from typing import Optional

class GeminiService:
    """Service để gọi Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_presentation_text(self, slide_content: str, language: str = 'vi') -> str:
        """
        Tạo text thuyết trình từ nội dung slide
        
        Args:
            slide_content: Nội dung raw từ slide
            language: Ngôn ngữ output (vi, en, ...)
        
        Returns:
            str: Text thuyết trình đã được generate
        """
        prompt = f"""
        Bạn là một chuyên gia tạo nội dung thuyết trình. 
        Dựa vào nội dung slide sau, hãy tạo ra một đoạn text thuyết trình tự nhiên, 
        dễ hiểu, phù hợp để nói trước đám đông.
        
        Nội dung slide:
        {slide_content}
        
        Yêu cầu:
        - Text phải tự nhiên, như đang nói chuyện
        - Độ dài phù hợp (khoảng 1-2 phút khi nói)
        - Sử dụng ngôn ngữ {language}
        - Không cần lặp lại tiêu đề slide
        - Tập trung vào giải thích và mở rộng nội dung
        
        Text thuyết trình:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def enhance_text(self, user_text: str, instruction: str = "") -> str:
        """
        Cải thiện text dựa trên instruction của user
        
        Args:
            user_text: Text hiện tại
            instruction: Hướng dẫn cải thiện (vd: "làm ngắn gọn hơn", "thêm ví dụ")
        
        Returns:
            str: Text đã được cải thiện
        """
        if not instruction:
            instruction = "Cải thiện text này để tự nhiên và dễ hiểu hơn"
        
        prompt = f"""
        {instruction}
        
        Text hiện tại:
        {user_text}
        
        Text cải thiện:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
```

---

## 5. Code Mẫu - utils/tts_service.py (VieNeu-TTS)

```python
from vieneu import Vieneu
import os
from typing import Optional, List, Tuple
from pydub import AudioSegment

class TTSService:
    """Service để chuyển text sang speech sử dụng VieNeu-TTS"""
    
    def __init__(
        self, 
        output_dir: str = 'static/audio',
        mode: str = 'local',  # 'local' hoặc 'remote'
        model_name: str = 'pnnbao-ump/VieNeu-TTS',
        api_base: Optional[str] = None  # Cho remote mode
    ):
        """
        Initialize VieNeu-TTS service
        
        Args:
            output_dir: Thư mục lưu audio output
            mode: 'local' (load model local) hoặc 'remote' (connect to server)
            model_name: Tên model trên HuggingFace
            api_base: URL của remote server (nếu dùng remote mode)
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize VieNeu-TTS
        if mode == 'remote' and api_base:
            self.tts = Vieneu(mode='remote', api_base=api_base, model_name=model_name)
        else:
            # Local mode - load model locally
            self.tts = Vieneu(mode='local', model_name=model_name)
    
    def list_available_voices(self) -> List[Tuple[str, str]]:
        """
        Lấy danh sách các preset voices có sẵn
        
        Returns:
            List[Tuple[str, str]]: [(description, voice_id), ...]
        """
        try:
            return self.tts.list_preset_voices()
        except Exception as e:
            raise Exception(f"Error listing voices: {str(e)}")
    
    def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        ref_audio: Optional[str] = None,  # Cho voice cloning
        ref_text: Optional[str] = None,   # Reference text cho cloning
        output_filename: Optional[str] = None
    ) -> str:
        """
        Chuyển text sang audio file sử dụng VieNeu-TTS
        
        Args:
            text: Text cần chuyển
            voice_id: ID của preset voice (nếu None thì dùng default)
            ref_audio: Đường dẫn audio mẫu cho voice cloning (optional)
            ref_text: Text tương ứng với ref_audio (cho voice cloning)
            output_filename: Tên file output (nếu None thì tự generate)
        
        Returns:
            str: Đường dẫn đến file audio
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if output_filename is None:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_filename = f"vieneu_{text_hash}.wav"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            # Nếu có voice_id, lấy preset voice
            voice_data = None
            if voice_id:
                voice_data = self.tts.get_preset_voice(voice_id)
            
            # Generate audio
            if ref_audio and ref_text:
                # Voice cloning mode
                audio_spec = self.tts.infer(
                    text=text,
                    ref_audio=ref_audio,
                    ref_text=ref_text
                )
            elif voice_data:
                # Preset voice mode
                audio_spec = self.tts.infer(text=text, voice=voice_data)
            else:
                # Default voice
                audio_spec = self.tts.infer(text=text)
            
            # Save audio
            self.tts.save(audio_spec, output_path)
            return output_path
            
        except Exception as e:
            raise Exception(f"VieNeu-TTS error: {str(e)}")
    
    def combine_audio_files(self, audio_files: list, output_path: str) -> str:
        """
        Kết hợp nhiều audio files thành một
        
        Args:
            audio_files: List đường dẫn đến các file audio
            output_path: Đường dẫn file output
        
        Returns:
            str: Đường dẫn file output
        """
        if not audio_files:
            raise ValueError("Audio files list cannot be empty")
        
        combined = AudioSegment.empty()
        
        for audio_file in audio_files:
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            # Load audio (support mp3, wav)
            ext = os.path.splitext(audio_file)[1].lower()
            if ext == '.mp3':
                audio = AudioSegment.from_mp3(audio_file)
            elif ext == '.wav':
                audio = AudioSegment.from_wav(audio_file)
            else:
                audio = AudioSegment.from_file(audio_file)
            
            # Add small silence between segments (500ms)
            if len(combined) > 0:
                silence = AudioSegment.silent(duration=500)
                combined += silence
            
            combined += audio
        
        # Export
        combined.export(output_path, format="wav")
        return output_path
```

---

## 6. Code Mẫu - utils/video_composer.py

```python
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, 
    CompositeVideoClip, concatenate_videoclips
)
from PIL import Image
import os
from typing import List, Dict, Optional

class VideoComposer:
    """Compose video presentation từ slides và talking head videos"""
    
    def __init__(self, output_dir: str = 'static/results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_presentation_video(
        self,
        slides: List[Dict],
        output_filename: str,
        transition_duration: float = 1.0,
        slide_duration: Optional[float] = None
    ) -> str:
        """
        Tạo video presentation từ slides
        
        Args:
            slides: List[{
                'slide_num': int,
                'image_path': str (path to slide image),
                'video_path': str (path to talking head video),
                'audio_path': str (path to audio),
                'duration': float (duration in seconds, optional)
            }]
            output_filename: Tên file output
            transition_duration: Thời gian transition giữa slides (seconds)
            slide_duration: Duration cố định cho mỗi slide (nếu None thì dùng audio duration)
        
        Returns:
            str: Đường dẫn đến video output
        """
        video_clips = []
        
        for idx, slide in enumerate(slides):
            # Load slide image
            if not os.path.exists(slide['image_path']):
                raise FileNotFoundError(f"Slide image not found: {slide['image_path']}")
            
            slide_image = ImageClip(slide['image_path'])
            
            # Load talking head video (nếu có)
            talking_head = None
            if slide.get('video_path') and os.path.exists(slide['video_path']):
                talking_head = VideoFileClip(slide['video_path'])
            
            # Determine duration
            if slide_duration:
                duration = slide_duration
            elif slide.get('duration'):
                duration = slide['duration']
            elif talking_head:
                duration = talking_head.duration
            elif slide.get('audio_path') and os.path.exists(slide['audio_path']):
                audio = AudioFileClip(slide['audio_path'])
                duration = audio.duration
                audio.close()
            else:
                duration = 5.0  # Default 5 seconds
            
            # Resize slide image to match video size (if talking head exists)
            if talking_head:
                # Resize slide to fit alongside talking head
                # Example: talking head on right, slide on left
                slide_image = slide_image.resize(height=talking_head.h)
                # Position slide on left side
                slide_image = slide_image.set_position(('left', 'center'))
                slide_image = slide_image.set_duration(duration)
                
                # Position talking head on right side
                talking_head = talking_head.set_position(('right', 'center'))
                talking_head = talking_head.set_duration(duration)
                
                # Composite
                composite = CompositeVideoClip([slide_image, talking_head], size=(1920, 1080))
            else:
                # Just slide image, resize to standard size
                slide_image = slide_image.resize((1920, 1080))
                slide_image = slide_image.set_duration(duration)
                composite = slide_image
            
            # Add audio if available
            if slide.get('audio_path') and os.path.exists(slide['audio_path']):
                audio = AudioFileClip(slide['audio_path'])
                # Trim audio to match video duration
                if audio.duration > duration:
                    audio = audio.subclip(0, duration)
                composite = composite.set_audio(audio)
            
            video_clips.append(composite)
        
        # Concatenate all clips
        if len(video_clips) == 1:
            final_video = video_clips[0]
        else:
            final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Export
        output_path = os.path.join(self.output_dir, output_filename)
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        
        # Cleanup
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        return output_path
    
    def add_subtitles(
        self,
        video_path: str,
        texts: List[Dict],
        output_path: str,
        font_size: int = 40,
        font_color: str = 'white'
    ) -> str:
        """
        Thêm subtitles vào video
        
        Args:
            video_path: Đường dẫn video gốc
            texts: List[{'start': float, 'end': float, 'text': str}]
            output_path: Đường dẫn output
            font_size: Kích thước font
            font_color: Màu chữ
        
        Returns:
            str: Đường dẫn output
        """
        from moviepy.editor import TextClip
        
        video = VideoFileClip(video_path)
        subtitle_clips = []
        
        for text_data in texts:
            txt_clip = TextClip(
                text_data['text'],
                fontsize=font_size,
                color=font_color,
                font='Arial-Bold'
            ).set_position(('center', 'bottom')).set_duration(
                text_data['end'] - text_data['start']
            ).set_start(text_data['start'])
            
            subtitle_clips.append(txt_clip)
        
        final_video = CompositeVideoClip([video] + subtitle_clips)
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        final_video.close()
        
        return output_path
```

---

## 7. Updated app.py - Routes mẫu

```python
from flask import Flask, request, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from utils.presentation_reader import PresentationReader
from utils.gemini_service import GeminiService
from utils.tts_service import TTSService
from utils.video_generator import VideoGenerator
from utils.video_composer import VideoComposer

app = Flask(__name__)

# Initialize services
gemini_service = GeminiService()
tts_service = TTSService()
video_generator = VideoGenerator()
video_composer = VideoComposer()

# Storage for presentations (in production, use database)
presentations = {}

@app.route('/api/upload-presentation', methods=['POST'])
def upload_presentation():
    """Upload file PPT/PDF"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    pres_id = str(uuid.uuid4())
    upload_dir = f'static/uploads/presentations/{pres_id}'
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    # Read presentation
    try:
        reader = PresentationReader()
        slides = reader.extract_text_from_file(file_path)
        
        # Store presentation data
        presentations[pres_id] = {
            'id': pres_id,
            'filename': filename,
            'file_path': file_path,
            'slides': slides,
            'type': os.path.splitext(filename)[1].lower()
        }
        
        return jsonify({
            'success': True,
            'presentation_id': pres_id,
            'slides': slides
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-text', methods=['POST'])
def generate_text():
    """Generate text với Gemini"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    presentation = presentations[pres_id]
    slide = next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)
    
    if not slide:
        return jsonify({'success': False, 'error': 'Slide not found'}), 404
    
    try:
        generated_text = gemini_service.generate_presentation_text(slide['content'])
        
        # Update slide
        slide['generated_text'] = generated_text
        if 'edited_text' not in slide:
            slide['edited_text'] = generated_text
        
        return jsonify({
            'success': True,
            'text': generated_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio từ text"""
    data = request.json
    pres_id = data.get('presentation_id')
    slide_num = data.get('slide_num')
    
    if pres_id not in presentations:
        return jsonify({'success': False, 'error': 'Presentation not found'}), 404
    
    presentation = presentations[pres_id]
    slide = next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)
    
    if not slide or 'edited_text' not in slide:
        return jsonify({'success': False, 'error': 'Slide or text not found'}), 404
    
    try:
        audio_path = tts_service.text_to_speech(
            slide['edited_text'],
            lang='vi',
            output_filename=f"{pres_id}_slide_{slide_num}.mp3"
        )
        
        slide['audio_path'] = audio_path
        
        return jsonify({
            'success': True,
            'audio_url': f'/static/audio/{os.path.basename(audio_path)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ... (các routes khác tương tự)
```

---

## 8. Frontend - Multi-step Form Structure

```html
<!-- templates/presentation.html -->
<div class="container">
  <!-- Step 1: Upload Presentation -->
  <div id="step1" class="step">
    <h2>Bước 1: Upload Presentation</h2>
    <input type="file" accept=".pptx,.ppt,.pdf" id="presentationFile">
    <button onclick="uploadPresentation()">Upload</button>
  </div>
  
  <!-- Step 2: Generate & Edit Text -->
  <div id="step2" class="step" style="display:none;">
    <h2>Bước 2: Generate & Edit Text</h2>
    <div id="slidesList"></div>
  </div>
  
  <!-- Step 3: Upload Avatar -->
  <div id="step3" class="step" style="display:none;">
    <h2>Bước 3: Upload Avatar</h2>
    <input type="file" accept="image/*" id="avatarFile">
    <button onclick="uploadAvatar()">Upload Avatar</button>
  </div>
  
  <!-- Step 4: Generate Audio & Video -->
  <div id="step4" class="step" style="display:none;">
    <h2>Bước 4: Generate Audio & Video</h2>
    <button onclick="generateAllAudio()">Generate All Audio</button>
    <button onclick="generateAllVideos()">Generate All Videos</button>
  </div>
  
  <!-- Step 5: Compose Final Video -->
  <div id="step5" class="step" style="display:none;">
    <h2>Bước 5: Compose Final Video</h2>
    <button onclick="composeVideo()">Compose Video</button>
    <video id="finalVideo" controls style="display:none;"></video>
  </div>
</div>
```

---

## 9. Environment Variables (.env)

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Flask
FLASK_ENV=development
FLASK_DEBUG=True

# Paths
UPLOAD_FOLDER=static/uploads
RESULT_FOLDER=static/results
```

---

Đây là cấu trúc code mẫu để bạn có thể bắt đầu implement. Mỗi service đã được tách riêng để dễ maintain và test.

