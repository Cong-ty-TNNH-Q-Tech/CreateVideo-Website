# Plan Triển Khai Tính Năng Tạo Video Thuyết Trình

## Tổng Quan
Mở rộng ứng dụng hiện tại để tạo video thuyết trình tự động từ file PPT/PDF với avatar nói chuyện.

---

## BƯỚC 1: Upload và Đọc File PPT/PDF

### 1.1 Dependencies
```txt
python-pptx==0.6.21      # Đọc file PowerPoint
pypdf==3.17.0             # Đọc file PDF
```

### 1.2 Cấu trúc thư mục
```
CreateVideo-WBước 1: Người dùng sẽ upload file ppt hoặc pdf lên. Với file ppt thì sử dụng thư viện python-pptx để đọc content trong từng slide. Còn PDF thì sử dụng thư viện pypdf để đọc nội dung từng trang.
Bước 2: Với mỗi slide (trang) nội dung thì gọi  gemini API để tạo ra text thuyết trình. Sau đó show phần text đó lên cho người dùng sửa lại.
Bước 3: Sử dụng thư viện gTTS để biến text sang speech.
Bước 4: Người dùng có thể upload ảnh  chân dung hoặc avatar lên và chúng ta sử dụng mô hình sadtalker trong huggingface để tạo video mấp máy mồm.
Bước 5: Tạo video thì có nhiều thư viện như moviepy hay ffmpeg.ebsite/
├── static/
│   ├── uploads/
│   │   ├── presentations/    # Lưu file PPT/PDF
│   │   └── avatars/          # Lưu ảnh avatar
│   ├── audio/                # Lưu audio từ gTTS
│   └── results/              # Video kết quả
```

### 1.3 Backend Implementation
**File: `app.py` - Thêm routes:**
- `POST /upload-presentation`: Upload file PPT/PDF
- `GET /presentation/<id>/slides`: Lấy danh sách slides/pages
- `GET /presentation/<id>/slide/<slide_num>/content`: Lấy nội dung slide cụ thể

**File mới: `utils/presentation_reader.py`**
```python
class PresentationReader:
    def read_pptx(file_path) -> List[dict]
    def read_pdf(file_path) -> List[dict]
    def extract_text_from_slide(slide) -> str
    def extract_text_from_page(page) -> str
```

### 1.4 Frontend
- Form upload file với accept=".pptx,.ppt,.pdf"
- Hiển thị preview slides/pages sau khi upload
- List slides với thumbnail (nếu có)

---

## BƯỚC 2: Tích Hợp Gemini API

### 2.1 Dependencies
```txt
google-generativeai==0.3.0    # Gemini API
```

### 2.2 Environment Variables
```env
GEMINI_API_KEY=your_api_key_here
```

### 2.3 Backend Implementation
**File mới: `utils/gemini_service.py`**
```python
class GeminiService:
    def __init__(api_key)
    def generate_presentation_text(slide_content: str) -> str
    def enhance_text(user_text: str, instruction: str) -> str
```

**File: `app.py` - Thêm routes:**
- `POST /generate-text`: Gọi Gemini để tạo text từ slide content
- `POST /save-text`: Lưu text đã chỉnh sửa của người dùng
- `GET /presentation/<id>/slide/<num>/text`: Lấy text của slide

### 2.4 Frontend
- Textarea hiển thị text từ Gemini
- Cho phép edit text
- Button "Generate Text" để gọi lại Gemini
- Button "Save" để lưu text đã chỉnh sửa
- Hiển thị loading khi gọi API

---

## BƯỚC 3: Text-to-Speech với VieNeu-TTS

### 3.1 Dependencies
```txt
vieneu-tts                    # VieNeu-TTS (Vietnamese TTS với voice cloning)
# Hoặc cài từ GitHub:
# pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
pydub==0.25.1                 # Xử lý audio (optional)
torch                         # PyTorch (required for VieNeu-TTS)
```

### 3.2 Ưu điểm của VieNeu-TTS so với gTTS:
- ✅ **Chất lượng tốt hơn**: Model chuyên biệt cho tiếng Việt
- ✅ **Voice Cloning**: Có thể clone giọng nói từ audio mẫu
- ✅ **On-device**: Chạy local, không cần internet
- ✅ **Real-time**: Hỗ trợ inference real-time
- ✅ **24kHz audio**: Chất lượng audio cao
- ✅ **Nhiều preset voices**: Có sẵn nhiều giọng nói
- ✅ **License**: Apache 2.0 (free to use cho model 0.5B)

### 3.3 Backend Implementation
**File mới: `utils/tts_service.py`**
```python
from vieneu import Vieneu
import os

class TTSService:
    def __init__(self, mode='local', model_name='pnnbao-ump/VieNeu-TTS'):
        # Local mode: Load model locally
        # Remote mode: Connect to remote server
        self.tts = Vieneu(mode=mode, model_name=model_name)
    
    def text_to_speech(
        self, 
        text: str, 
        voice_id: str = None,  # Preset voice ID
        ref_audio: str = None,  # For voice cloning
        ref_text: str = None,   # Reference text for cloning
        output_path: str = None
    ) -> str
    
    def list_available_voices(self) -> List[tuple]  # (description, voice_id)
    def combine_audio_files(audio_files: List[str], output_path: str) -> str
```

**File: `app.py` - Thêm routes:**
- `POST /generate-audio`: Tạo audio từ text
- `POST /generate-all-audio`: Tạo audio cho tất cả slides
- `GET /audio/<filename>`: Stream audio file

### 3.4 Frontend
- Button "Generate Audio" cho từng slide
- Button "Generate All Audio" cho tất cả slides
- **Voice Selection**: Dropdown để chọn giọng nói (preset voices)
- **Voice Cloning Option**: Upload audio mẫu để clone giọng (optional)
- Audio player để preview
- Progress bar khi generate nhiều audio

---

## BƯỚC 4: Tích Hợp SadTalker với Avatar

### 4.1 Backend Implementation
**File: `app.py` - Cập nhật routes:**
- `POST /upload-avatar`: Upload ảnh avatar
- `POST /generate-video`: Tạo video với SadTalker (đã có, cần mở rộng)
  - Input: avatar image + audio file
  - Output: video file

**File mới: `utils/video_generator.py`**
```python
class VideoGenerator:
    def generate_talking_head(avatar_path: str, audio_path: str, output_path: str)
    def batch_generate_videos(avatar_path: str, audio_files: List[str], output_dir: str)
```

### 4.2 Frontend
- Upload avatar image
- Preview avatar
- Button "Generate Video" cho từng slide
- Button "Generate All Videos" cho tất cả slides
- Video preview player

---

## BƯỚC 5: Tạo Video Cuối Cùng

### 5.1 Dependencies
```txt
moviepy==1.0.3               # Video editing
Pillow==10.0.0                # Image processing (đã có trong dependencies khác)
```

### 5.2 Backend Implementation
**File mới: `utils/video_composer.py`**
```python
class VideoComposer:
    def create_presentation_video(
        slides: List[dict],           # [{image_path, video_path, audio_path, duration}]
        output_path: str,
        transition_duration: float = 1.0
    ) -> str
    
    def add_subtitles(video_path: str, texts: List[str], output_path: str) -> str
    def add_background_music(video_path: str, music_path: str, output_path: str) -> str
```

**File: `app.py` - Thêm routes:**
- `POST /compose-video`: Tạo video presentation hoàn chỉnh
- `GET /video/<filename>`: Stream video file
- `POST /download-video/<id>`: Download video

### 5.3 Frontend
- Button "Compose Final Video"
- Preview video cuối cùng
- Download button
- Progress indicator cho quá trình compose

---

## WORKFLOW TỔNG THỂ

```
1. User upload PPT/PDF
   ↓
2. System extract content từ từng slide/page
   ↓
3. For each slide:
   a. Gọi Gemini API → Generate text
   b. User review & edit text
   c. Save text
   ↓
4. User upload avatar image
   ↓
5. For each slide:
   a. Text → gTTS → Audio file
   b. Avatar + Audio → SadTalker → Talking head video
   ↓
6. Compose final video:
   - Combine slides (images hoặc video)
   - Sync với talking head videos
   - Add transitions
   - Add subtitles (optional)
   ↓
7. Return final video
```

---

## CẤU TRÚC DATABASE (Optional - có thể dùng JSON file)

Nếu không dùng database, có thể lưu metadata trong JSON:

```json
{
  "presentation_id": "uuid",
  "filename": "presentation.pptx",
  "type": "pptx",
  "slides": [
    {
      "slide_num": 1,
      "content": "raw text from slide",
      "generated_text": "text from Gemini",
      "edited_text": "user edited text",
      "audio_path": "path/to/audio.wav",
      "video_path": "path/to/video.mp4",
      "status": "completed"
    }
  ],
  "avatar_path": "path/to/avatar.jpg",
  "final_video_path": "path/to/final.mp4",
  "created_at": "timestamp"
}
```

---

## API ROUTES TỔNG HỢP

### Presentation Management
- `POST /api/upload-presentation` - Upload PPT/PDF
- `GET /api/presentation/<id>` - Get presentation info
- `GET /api/presentation/<id>/slides` - Get all slides

### Text Generation
- `POST /api/generate-text` - Generate text với Gemini
- `POST /api/save-text` - Save edited text
- `GET /api/presentation/<id>/slide/<num>/text` - Get text

### Audio Generation
- `POST /api/generate-audio` - Generate audio từ text
- `POST /api/generate-all-audio` - Generate all audio

### Avatar & Video
- `POST /api/upload-avatar` - Upload avatar
- `POST /api/generate-video` - Generate talking head video
- `POST /api/generate-all-videos` - Generate all videos

### Final Video
- `POST /api/compose-video` - Compose final video
- `GET /api/video/<filename>` - Stream video
- `GET /api/download/<id>` - Download video

---

## FRONTEND STRUCTURE

### Multi-step Form
```
Step 1: Upload Presentation
  - File upload
  - Preview slides

Step 2: Generate & Edit Text
  - List slides
  - Text editor for each slide
  - Generate button

Step 3: Upload Avatar
  - Image upload
  - Preview

Step 4: Generate Audio & Video
  - Generate audio buttons
  - Generate video buttons
  - Preview sections

Step 5: Compose Final Video
  - Compose button
  - Final video preview
  - Download button
```

---

## ERROR HANDLING

### Các lỗi cần xử lý:
1. File upload errors (size, format)
2. Gemini API errors (rate limit, invalid key)
3. VieNeu-TTS errors (model loading, GPU/CPU memory, voice cloning issues)
4. SadTalker errors (model loading, GPU memory)
5. Video composition errors (file corruption, format issues)

### Error Response Format:
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

---

## PERFORMANCE OPTIMIZATION

1. **Async Processing**: Sử dụng Celery hoặc background tasks cho:
   - Text generation
   - Audio generation
   - Video generation
   - Final composition

2. **Caching**: Cache Gemini responses cho cùng nội dung

3. **Batch Processing**: Process nhiều slides cùng lúc khi có thể

4. **Progress Tracking**: WebSocket hoặc polling để update progress

---

## SECURITY CONSIDERATIONS

1. File upload validation (size, type, malware scan)
2. API key protection (env variables, không hardcode)
3. Rate limiting cho API calls
4. Sanitize user input (text editing)
5. Secure file storage

---

## TESTING PLAN

1. Unit tests cho từng service
2. Integration tests cho workflow
3. Test với các file PPT/PDF khác nhau
4. Test error handling
5. Performance testing với large files

---

## DEPLOYMENT CHECKLIST

- [ ] Install all dependencies
- [ ] Setup environment variables
- [ ] Download SadTalker models
- [ ] Test Gemini API connection
- [ ] Test VieNeu-TTS functionality (local hoặc remote mode)
- [ ] Download VieNeu-TTS models (nếu dùng local mode)
- [ ] Test video generation
- [ ] Setup file storage
- [ ] Configure CORS (nếu cần)
- [ ] Setup logging
- [ ] Error monitoring

---

## TIMELINE ƯỚC TÍNH

- Bước 1: 2-3 giờ
- Bước 2: 3-4 giờ
- Bước 3: 2-3 giờ
- Bước 4: 2-3 giờ (tận dụng code hiện có)
- Bước 5: 4-5 giờ
- Testing & Debugging: 3-4 giờ

**Tổng: ~16-22 giờ**

---

## NOTES

1. Có thể sử dụng Hugging Face Spaces cho SadTalker thay vì local model
2. Cân nhắc sử dụng queue system (Redis + Celery) cho production
3. Có thể thêm tính năng export slides thành images nếu cần
4. Cân nhắc thêm tính năng preview real-time khi edit text

