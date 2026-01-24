# Hướng Dẫn Tích Hợp VieNeu-TTS

## Tổng Quan

**VieNeu-TTS** là một model Text-to-Speech chuyên biệt cho tiếng Việt với khả năng voice cloning. Thay vì sử dụng gTTS, chúng ta sẽ sử dụng VieNeu-TTS để có chất lượng tốt hơn.

**GitHub**: https://github.com/pnnbao97/VieNeu-TTS

---

## Ưu Điểm Của VieNeu-TTS

### So với gTTS:
- ✅ **Chất lượng tốt hơn**: Model được train chuyên biệt cho tiếng Việt
- ✅ **Voice Cloning**: Có thể clone giọng nói từ audio mẫu
- ✅ **On-device**: Chạy local, không cần internet (local mode)
- ✅ **Real-time**: Hỗ trợ inference real-time
- ✅ **24kHz audio**: Chất lượng audio cao hơn
- ✅ **Nhiều preset voices**: Có sẵn nhiều giọng nói khác nhau
- ✅ **Free License**: Apache 2.0 cho model 0.5B (free to use)

---

## Cài Đặt

### Option 1: Cài từ GitHub (Recommended)
```bash
pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
```

### Option 2: Cài từ PyPI (nếu có)
```bash
pip install vieneu-tts
```

### Dependencies
```txt
torch>=2.0.0
transformers
huggingface_hub
```

---

## Cách Sử Dụng

### 1. Local Mode (Load model trên máy)

```python
from vieneu import Vieneu

# Initialize
tts = Vieneu(mode='local', model_name='pnnbao-ump/VieNeu-TTS')

# List available voices
voices = tts.list_preset_voices()
for desc, voice_id in voices:
    print(f"{desc} (ID: {voice_id})")

# Generate audio với preset voice
voice_data = tts.get_preset_voice(voices[0][1])  # Chọn voice đầu tiên
audio_spec = tts.infer(text="Xin chào, đây là VieNeu-TTS", voice=voice_data)
tts.save(audio_spec, "output.wav")

# Voice cloning (từ audio mẫu)
audio_spec = tts.infer(
    text="Đây là giọng nói được clone",
    ref_audio="path/to/reference_audio.wav",
    ref_text="Text tương ứng với reference audio"
)
tts.save(audio_spec, "cloned_output.wav")
```

### 2. Remote Mode (Kết nối đến server)

Nếu bạn deploy VieNeu-TTS trên server riêng (Docker hoặc HuggingFace Spaces):

```python
from vieneu import Vieneu

# Initialize remote mode
tts = Vieneu(
    mode='remote',
    api_base='http://your-server:23333/v1',
    model_name='pnnbao-ump/VieNeu-TTS'
)

# Sử dụng tương tự như local mode
audio_spec = tts.infer(text="Text cần chuyển")
tts.save(audio_spec, "output.wav")
```

**Lợi ích Remote Mode:**
- Không cần GPU tại máy client
- Model chạy trên server mạnh
- Dễ scale cho nhiều users

---

## Tích Hợp Vào Dự Án

### 1. Cập nhật `requirements.txt`

```txt
# Text-to-Speech - VieNeu-TTS
vieneu-tts
# Hoặc: pip install git+https://github.com/pnnbao97/VieNeu-TTS.git
torch>=2.0.0
pydub==0.25.1
```

### 2. Tạo Service Wrapper

Xem file `CODE_STRUCTURE.md` phần `utils/tts_service.py` để xem code mẫu đầy đủ.

### 3. Cập nhật Routes trong `app.py`

```python
from utils.tts_service import TTSService

# Initialize service
tts_service = TTSService(
    output_dir='static/audio',
    mode='local',  # hoặc 'remote'
    model_name='pnnbao-ump/VieNeu-TTS'
)

@app.route('/api/list-voices', methods=['GET'])
def list_voices():
    """Lấy danh sách voices có sẵn"""
    try:
        voices = tts_service.list_available_voices()
        return jsonify({
            'success': True,
            'voices': [{'description': desc, 'id': vid} for desc, vid in voices]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio với VieNeu-TTS"""
    data = request.json
    text = data.get('text')
    voice_id = data.get('voice_id')  # Optional
    ref_audio = data.get('ref_audio')  # Optional - cho voice cloning
    ref_text = data.get('ref_text')  # Optional
    
    try:
        audio_path = tts_service.text_to_speech(
            text=text,
            voice_id=voice_id,
            ref_audio=ref_audio,
            ref_text=ref_text
        )
        
        return jsonify({
            'success': True,
            'audio_url': f'/static/audio/{os.path.basename(audio_path)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 4. Frontend - Thêm Voice Selection

```html
<!-- Voice Selection Dropdown -->
<div class="form-group">
    <label>Chọn Giọng Nói:</label>
    <select id="voiceSelect" class="form-control">
        <option value="">Giọng mặc định</option>
        <!-- Populate từ API -->
    </select>
</div>

<!-- Voice Cloning (Optional) -->
<div class="form-group">
    <label>Voice Cloning (Tùy chọn):</label>
    <input type="file" id="refAudio" accept="audio/*">
    <input type="text" id="refText" placeholder="Text tương ứng với audio mẫu">
</div>
```

---

## Các Model Variants

VieNeu-TTS có nhiều model variants:

| Model | Size | Quality | Speed | License |
|-------|------|---------|-------|---------|
| VieNeu-TTS (0.5B) | 0.5B | ⭐⭐⭐⭐⭐ | Fast | Apache 2.0 (Free) |
| VieNeu-TTS-0.3B | 0.3B | ⭐⭐⭐⭐ | Ultra Fast | CC BY-NC 4.0 (Non-commercial) |
| VieNeu-TTS-q8-gguf | GGUF Q8 | ⭐⭐⭐⭐ | Fast | Apache 2.0 |

**Khuyến nghị**: Sử dụng `pnnbao-ump/VieNeu-TTS` (0.5B) cho production vì:
- License free to use
- Chất lượng tốt nhất
- Tốc độ đủ nhanh

---

## Performance Tips

### 1. Local Mode
- **GPU**: Nhanh hơn nhiều, khuyến nghị nếu có GPU
- **CPU**: Vẫn chạy được nhưng chậm hơn
- **Memory**: Cần ~2-4GB RAM cho model 0.5B

### 2. Remote Mode
- Deploy model trên server có GPU
- Client chỉ cần gửi request, không cần load model
- Phù hợp cho web app

### 3. Caching
- Cache audio đã generate để tránh generate lại cùng text
- Sử dụng hash của text làm key

---

## Troubleshooting

### Lỗi: "Model not found"
```bash
# Đảm bảo đã cài đặt đúng
pip install git+https://github.com/pnnbao97/VieNeu-TTS.git

# Hoặc download model manually
from huggingface_hub import snapshot_download
snapshot_download("pnnbao-ump/VieNeu-TTS")
```

### Lỗi: "CUDA out of memory"
- Giảm batch size
- Sử dụng CPU mode: `device='cpu'`
- Hoặc dùng model nhỏ hơn (0.3B)

### Lỗi: "Remote connection failed"
- Kiểm tra server có đang chạy không
- Kiểm tra URL và port
- Kiểm tra firewall

---

## License

- **VieNeu-TTS (0.5B)**: Apache 2.0 - **Free to use** (commercial OK)
- **VieNeu-TTS-0.3B**: CC BY-NC 4.0 - **Non-commercial only**

**Khuyến nghị**: Sử dụng model 0.5B cho dự án commercial.

---

## References

- **GitHub**: https://github.com/pnnbao97/VieNeu-TTS
- **HuggingFace**: https://huggingface.co/pnnbao-ump/VieNeu-TTS
- **Demo**: https://huggingface.co/spaces/pnnbao-ump/VieNeu-TTS

---

## Migration từ gTTS

Nếu bạn đã có code sử dụng gTTS, migration rất đơn giản:

### Before (gTTS):
```python
from gtts import gTTS
tts = gTTS(text="Hello", lang='vi')
tts.save("output.mp3")
```

### After (VieNeu-TTS):
```python
from vieneu import Vieneu
tts = Vieneu(mode='local')
audio = tts.infer(text="Hello")
tts.save(audio, "output.wav")
```

Chỉ cần thay đổi cách gọi API, logic workflow giữ nguyên!

