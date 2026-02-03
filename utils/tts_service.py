"""
Service để chuyển text sang speech sử dụng VieNeu-TTS
"""
import os
from typing import Optional, List, Tuple

# Try to import VieNeu-TTS
try:
    from vieneu import Vieneu
    VIENEU_AVAILABLE = True
except ImportError:
    VIENEU_AVAILABLE = False
    print("Warning: VieNeu-TTS not installed. Install with: pip install git+https://github.com/pnnbao97/VieNeu-TTS.git")

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
        if not VIENEU_AVAILABLE:
            raise ImportError(
                "VieNeu-TTS not installed. "
                "Install with: pip install git+https://github.com/pnnbao97/VieNeu-TTS.git"
            )
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize VieNeu-TTS
        try:
            if mode == 'remote' and api_base:
                self.tts = Vieneu(mode='remote', api_base=api_base, model_name=model_name)
            else:
                # Local mode - load model locally
                self.tts = Vieneu(mode='local', model_name=model_name)
        except Exception as e:
            raise Exception(f"Failed to initialize VieNeu-TTS: {str(e)}")
    
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
        if not text or not text.strip():
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
                if not os.path.exists(ref_audio):
                    raise FileNotFoundError(f"Reference audio not found: {ref_audio}")
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
    
    def combine_audio_files(self, audio_files: List[str], output_path: str) -> str:
        """
        Kết hợp nhiều audio files thành một
        
        Args:
            audio_files: List đường dẫn đến các file audio
            output_path: Đường dẫn file output
        
        Returns:
            str: Đường dẫn file output
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            raise ImportError("pydub is required for combining audio files. Install with: pip install pydub")
        
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




