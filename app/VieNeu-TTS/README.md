# VieNeu-TTS - Vietnamese Text-to-Speech

Thư viện TTS tiếng Việt được tích hợp cho dự án VideoTeaching.

**Source:** [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS)

## Cấu trúc

```
VieNeu-TTS/
├── vieneu/              # SDK core
│   ├── __init__.py
│   ├── core.py          # Main TTS classes
│   ├── serve.py         # Server utilities
│   └── assets/          # Preset voices & samples
├── vieneu_utils/        # Text processing utilities
│   ├── core_utils.py
│   ├── normalize_text.py
│   ├── phonemize_text.py
│   └── phoneme_dict.json
├── examples/            # Audio reference samples
├── config.yaml          # Model configurations
├── main.py              # Usage example
└── requirements.txt     # Dependencies
```

## Cách sử dụng

### Basic Usage

```python
from vieneu import Vieneu

# Initialize TTS engine
tts = Vieneu()

# Generate speech
text = "Xin chào, đây là VieNeu TTS."
audio = tts.infer(text=text)
tts.save(audio, "output.wav")
```

### With Voice Selection

```python
# List available voices
voices = tts.list_preset_voices()
for desc, voice_id in voices:
    print(f"{desc} (ID: {voice_id})")

# Use specific voice
voice_data = tts.get_preset_voice("Tuyen")
audio = tts.infer(text=text, voice=voice_data)
```

### Voice Cloning

```python
# Clone voice from audio sample (3-5 seconds)
audio = tts.infer(
    text="Văn bản cần đọc.",
    ref_audio="path/to/sample.wav",
    ref_text="Transcript của audio sample."
)
```

## Yêu cầu hệ thống

- **eSpeak NG**: Required for phonemization
  - Windows: Download `.msi` from [eSpeak NG Releases](https://github.com/espeak-ng/espeak-ng/releases)
  - macOS: `brew install espeak`
  - Ubuntu/Debian: `sudo apt install espeak-ng`

## License

Apache 2.0 (VieNeu-TTS 0.5B)
CC BY-NC 4.0 (VieNeu-TTS 0.3B - Non-commercial)
