"""
Audio Service for Text-to-Speech Generation

This service provides audio generation capabilities with VieNeu-TTS as primary option
and edge-tts (Microsoft Neural) as fallback, with gTTS as last resort.
"""

import os
import sys
import traceback
import uuid
import threading
from pathlib import Path
from typing import Optional, Tuple

# Language detection
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    # Set seed for consistent results across threads
    DetectorFactory.seed = 0
    # Pre-load language profiles now (avoids "Need to load profiles." in worker threads)
    try:
        detect("xin chào")
    except Exception:
        pass
    LANGDETECT_AVAILABLE = True
    print("✅ langdetect available for advanced language detection")
except ImportError:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception  # fallback so except clause doesn't break
    print("ℹ️  langdetect not available - using fallback language detection")
except Exception as e:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception
    print(f"ℹ️  langdetect error: {e} - using fallback detection")

# Add VieNeu-TTS to path for imports
vieneu_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VieNeu-TTS')
if vieneu_path not in sys.path:
    sys.path.append(vieneu_path)

class AudioService:
    """Service for generating audio from text with multi-language support"""
    
    # Language mapping for gTTS (fallback)
    SUPPORTED_LANGUAGES = {
        'vi': 'vi',     # Vietnamese
        'en': 'en',     # English  
        'zh': 'zh',     # Chinese
        'ja': 'ja',     # Japanese
        'ko': 'ko',     # Korean
        'th': 'th',     # Thai
        'fr': 'fr',     # French
        'de': 'de',     # German
        'es': 'es',     # Spanish
        'it': 'it',     # Italian
        'pt': 'pt',     # Portuguese
        'ru': 'ru',     # Russian
        'ar': 'ar',     # Arabic
        'hi': 'hi',     # Hindi
    }

    # Neural voice mapping for edge-tts (Microsoft Azure)
    EDGE_TTS_VOICES = {
        'vi': 'vi-VN-HoaiMyNeural',       # Vietnamese (female, natural)
        'en': 'en-US-JennyNeural',         # English US
        'zh': 'zh-CN-XiaoxiaoNeural',      # Chinese Simplified
        'ja': 'ja-JP-NanamiNeural',        # Japanese
        'ko': 'ko-KR-SunHiNeural',         # Korean
        'th': 'th-TH-PremwadeeNeural',     # Thai
        'fr': 'fr-FR-DeniseNeural',        # French
        'de': 'de-DE-KatjaNeural',         # German
        'es': 'es-ES-ElviraNeural',        # Spanish
        'it': 'it-IT-ElsaNeural',          # Italian
        'pt': 'pt-BR-FranciscaNeural',     # Portuguese Brazil
        'ru': 'ru-RU-SvetlanaNeural',      # Russian
        'ar': 'ar-EG-SalmaNeural',         # Arabic
        'hi': 'hi-IN-SwaraNeural',         # Hindi
    }
    
    def __init__(self, force_gtts=False):
        self.vieneu_engine = None
        self.vieneu_available = False
        self.preferred_voice = None
        self.force_gtts = force_gtts
        # Protects GPU/CPU model inference — only VieNeu acquires this
        self._vieneu_lock = threading.Lock()
        
        # Chỉ thử VieNeu-TTS nếu không bị force dùng gTTS
        if not force_gtts:
            self._init_vieneu()
        else:
            print("🎯 Force using gTTS - skipping VieNeu-TTS initialization")
    
    def _init_vieneu(self):
        """Initialize VieNeu-TTS engine with fast fail"""
        try:
            print("🚀 Quick VieNeu-TTS check...")
            
            # Quick check for VieNeu availability
            try:
                from vieneu import Vieneu
                print("  ✅ VieNeu module available")
            except ImportError as e:
                if "HubertModel" in str(e):
                    print("  ❌ VieNeu-TTS missing HubertModel dependencies")
                    print("  🎯 Using gTTS as primary TTS engine")
                else:
                    print(f"  ❌ VieNeu import failed: {e}")
                self.vieneu_available = False
                return
            
            # Try to initialize quickly
            try:
                print("  🔧 Quick VieNeu initialization...")
                # Auto-detect device: use CUDA if available
                import torch
                # Fix CUDA_VISIBLE_DEVICES misconfiguration:
                # If it's set to a non-existing index (e.g. =1 on a 1-GPU machine), reset to 0
                cvd = os.environ.get('CUDA_VISIBLE_DEVICES', '')
                if cvd not in ('', 'all', 'void', 'noDevFiles'):
                    try:
                        import subprocess as _sp
                        ngpu = int(_sp.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                           capture_output=True, text=True).stdout.strip().count('\n')) + 1
                        requested = [int(x) for x in cvd.split(',') if x.strip().lstrip('-').isdigit()]
                        if requested and max(requested) >= ngpu:
                            print(f"  ⚠️  CUDA_VISIBLE_DEVICES={cvd} invalid for {ngpu} GPU(s), resetting to 0")
                            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
                    except Exception:
                        pass
                cuda_available = torch.cuda.is_available()
                if not cuda_available:
                    try:
                        torch.cuda.init()
                    except Exception as cuda_err:
                        print(f"  ⚠️  CUDA init error: {cuda_err}")
                print(f"  🔍 torch: {torch.__version__}, CUDA: {cuda_available}, device_count: {torch.cuda.device_count()}")
                device = "cuda" if cuda_available else "cpu"
                print(f"  🖥️  Using device: {device}")
                # Best quality model per device:
                #   GPU → VieNeu-TTS-0.3B (PyTorch, ★★★★, no quantization loss)
                #   CPU → VieNeu-TTS-0.3B-q8-gguf (GGUF Q8, ★★★★, faster than Q4)
                if cuda_available:
                    backbone_repo = "pnnbao-ump/VieNeu-TTS-0.3B"
                else:
                    backbone_repo = "pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf"
                print(f"  📦 Model: {backbone_repo}")
                self.vieneu_engine = Vieneu(backbone_repo=backbone_repo, backbone_device=device, codec_device=device)
                
                # Get available voices quickly
                available_voices = self.vieneu_engine.list_preset_voices()
                if available_voices:
                    _, voice_id = available_voices[0]  # Just use first voice
                    self.preferred_voice = self.vieneu_engine.get_preset_voice(voice_id)
                    print(f"👤 Selected VieNeu voice: {available_voices[0][0]}")
                
                self.vieneu_available = True
                print("✅ VieNeu-TTS ready")
                
            except Exception as e:
                print(f"  ❌ VieNeu initialization failed: {e}")
                self.vieneu_available = False
                
        except Exception as e:
            print(f"⚠️  VieNeu-TTS not available: {e}")
            self.vieneu_available = False
    
    def detect_language(self, text: str) -> str:
        """Detect language of text and return appropriate language code"""
        if not text or len(text.strip()) < 10:
            return 'vi'  # Default to Vietnamese
        
        try:
            if LANGDETECT_AVAILABLE:
                try:
                    detected = detect(text)
                except LangDetectException as lde:
                    print(f"  ⚠️  langdetect exception: {lde}, defaulting to Vietnamese")
                    return 'vi'
                print(f"  🔍 Detected language: {detected}")
                
                # Map detected language to supported language
                if detected in self.SUPPORTED_LANGUAGES:
                    return detected
                elif detected in ['zh-cn', 'zh-tw']:
                    return 'zh'
                elif detected in ['pt-br']:
                    return 'pt'
                else:
                    # Fallback for unsupported languages
                    print(f"  ⚠️  Language {detected} not fully supported, using English")
                    return 'en'
            else:
                # Simple fallback language detection
                text_lower = text.lower()
                
                # Check for Vietnamese characters (diacritics)
                if any(char in text_lower for char in ['á', 'à', 'ả', 'ã', 'ạ', 'đ', 'ê', 'ô', 'ơ', 'ư']):
                    print("  🇻🇳 Detected Vietnamese (diacritics)")
                    return 'vi'
                
                # Check for common English words
                common_english_words = [
                    'the', 'and', 'is', 'in', 'you', 'that', 'it', 'for', 'with', 
                    'as', 'on', 'at', 'be', 'have', 'to', 'of', 'this', 'from', 
                    'or', 'by', 'not', 'but', 'are', 'was', 'were', 'been', 'has'
                ]
                words = text_lower.split()
                english_word_count = sum(1 for word in words if word in common_english_words)
                
                # If more than 20% are common English words, consider it English
                if len(words) > 0 and english_word_count / len(words) > 0.2:
                    print(f"  🇬🇧 Detected English ({english_word_count}/{len(words)} common words)")
                    return 'en'
                
                # Default to Vietnamese
                print("  🇻🇳 Defaulting to Vietnamese")
                return 'vi'
                    
        except Exception as e:
            print(f"  ⚠️  Language detection failed: {e}")
            return 'vi'  # Default to Vietnamese
    
    def should_use_vieneu(self, language: str) -> bool:
        """Determine if VieNeu-TTS should be used for this language"""
        return language == 'vi' and self.vieneu_available and not self.force_gtts
    
    def get_available_voices(self):
        """Get list of available VieNeu-TTS preset voices"""
        if not self.vieneu_available or not self.vieneu_engine:
            return []
        
        try:
            voices = self.vieneu_engine.list_preset_voices()
            # Returns list of tuples: [(name, id), ...]
            return [{'name': name, 'id': voice_id} for name, voice_id in voices]
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []
    
    def generate_audio(self, text: str, output_path: str, voice_type: str = None, voice_id: str = None, clone_voice_path: str = None) -> Tuple[bool, str]:
        """
        Generate audio from text using specified TTS engine
        
        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            voice_type: TTS engine to use ('vieneu', 'gtts', 'clone'). If None, auto-detect based on language
            voice_id: Optional preset voice ID for VieNeu-TTS
            clone_voice_path: Optional path to audio file for voice cloning
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Clean up text for TTS
            clean_text = self._clean_text_for_tts(text)
            if not clean_text.strip():
                return False, "No valid text provided"
            
            # Detect language
            detected_lang = self.detect_language(clean_text)
            print(f"🌐 Language: {detected_lang}")
            
            # If voice_type is explicitly set, use that engine
            if voice_type in ('gtts', 'edge'):
                # edge-tts (Microsoft Neural) — 'gtts' kept as backward-compat alias
                print("🎯 User selected edge-tts")
                if self._generate_with_edge_tts(clean_text, output_path, detected_lang, voice_id=voice_id):
                    return True, f"Generated using edge-tts ({voice_id or detected_lang})"
                else:
                    return False, f"edge-tts failed for language {detected_lang}"
                    
            elif voice_type == 'clone':
                # Force VieNeu with voice cloning
                print("🎯 User selected Voice Clone")
                if self._generate_with_vieneu(clean_text, output_path, voice_id, clone_voice_path):
                    return True, f"Generated using Voice Clone ({detected_lang})"
                else:
                    print("⚠️  Voice cloning failed, falling back to edge-tts...")
                    if self._generate_with_edge_tts(clean_text, output_path, detected_lang):
                        return True, f"Generated using edge-tts fallback ({detected_lang})"
                    else:
                        return False, "Both Voice Clone and edge-tts failed"
                        
            elif voice_type == 'vieneu':
                # Force VieNeu-TTS
                print("🎯 User selected VieNeu-TTS")
                if self._generate_with_vieneu(clean_text, output_path, voice_id, clone_voice_path):
                    return True, f"Generated using VieNeu-TTS ({detected_lang})"
                else:
                    print("⚠️  VieNeu-TTS failed, falling back to edge-tts...")
                    if self._generate_with_edge_tts(clean_text, output_path, detected_lang):
                        return True, f"Generated using edge-tts fallback ({detected_lang})"
                    else:
                        return False, "Both VieNeu-TTS and edge-tts failed"
            else:
                # Auto-detect based on language (legacy behavior)
                if self.should_use_vieneu(detected_lang):
                    # Dùng VieNeu-TTS cho tiếng Việt
                    if self._generate_with_vieneu(clean_text, output_path, voice_id, clone_voice_path):
                        return True, f"Generated using VieNeu-TTS ({detected_lang})"
                    else:
                        print("⚠️  VieNeu-TTS failed, falling back to edge-tts...")
                        if self._generate_with_edge_tts(clean_text, output_path, detected_lang):
                            return True, f"Generated using edge-tts fallback ({detected_lang})"
                        else:
                            return False, "Both VieNeu-TTS and edge-tts failed"
                else:
                    # Dùng edge-tts cho các ngôn ngữ khác
                    if self._generate_with_edge_tts(clean_text, output_path, detected_lang):
                        return True, f"Generated using edge-tts ({detected_lang})"
                    else:
                        return False, f"edge-tts failed for language {detected_lang}"
                
        except Exception as e:
            error_msg = f"Audio generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return False, error_msg
    
    def _generate_with_vieneu(self, text: str, output_path: str, voice_id: str = None, clone_voice_path: str = None) -> bool:
        """Generate audio using VieNeu-TTS engine (thread-safe: serializes GPU inference)"""
        try:
            if not self.vieneu_engine or not self.vieneu_available:
                return False

            print(f"🎧 Generating audio with VieNeu-TTS...")

            # Serialize GPU inference — gTTS threads are NOT blocked by this lock
            with self._vieneu_lock:
                # Determine which voice to use
                voice_to_use = None

                if clone_voice_path and os.path.exists(clone_voice_path):
                    print(f"  🎤 Using cloned voice from: {clone_voice_path}")
                    try:
                        voice_to_use = self.vieneu_engine.clone_voice(clone_voice_path)
                    except Exception as e:
                        print(f"  ⚠️ Voice cloning failed: {e}, using preset")

                if not voice_to_use and voice_id:
                    print(f"  👤 Using preset voice: {voice_id}")
                    try:
                        voice_to_use = self.vieneu_engine.get_preset_voice(voice_id)
                    except Exception as e:
                        print(f"  ⚠️ Failed to get voice {voice_id}: {e}")

                if not voice_to_use:
                    voice_to_use = self.preferred_voice
                    if voice_to_use:
                        print(f"  👤 Using default preferred voice")

                # GPU inference
                if voice_to_use:
                    audio_spec = self.vieneu_engine.infer(text=text, voice=voice_to_use)
                else:
                    audio_spec = self.vieneu_engine.infer(text=text)

            # Save outside lock — pure I/O
            self.vieneu_engine.save(audio_spec, output_path)
            print(f"✅ VieNeu-TTS audio saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ VieNeu-TTS failed: {e}")
            traceback.print_exc()
            return False
    
    def _generate_with_edge_tts(self, text: str, output_path: str, language: str = 'vi', voice_id: str = None) -> bool:
        """Generate audio using Microsoft Edge TTS (neural voices, free, requires internet).
        Falls back to gTTS if edge-tts is unavailable or fails.
        """
        try:
            import edge_tts
            import asyncio
            import concurrent.futures
            import tempfile

            # Use explicit voice_id if provided, otherwise pick by language
            voice = voice_id if voice_id else self.EDGE_TTS_VOICES.get(language, 'en-US-JennyNeural')
            print(f"🎧 Generating audio with edge-tts ({voice})...")

            if not text or len(text.strip()) < 3:
                print("  ❌ Text too short for TTS")
                return False

            # Save mp3 to temp, then convert to wav
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                temp_mp3 = tmp.name

            async def _run():
                communicate = edge_tts.Communicate(text, voice, rate="-5%")
                await communicate.save(temp_mp3)

            # Always run in a new thread with its own fresh event loop to avoid
            # conflicts with Flask's threaded WSGI environment
            def _sync_run():
                asyncio.run(_run())

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(_sync_run).result(timeout=60)

            if not os.path.exists(temp_mp3) or os.path.getsize(temp_mp3) == 0:
                print("  ❌ edge-tts produced no output")
                return False

            # Convert mp3 → wav
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(output_path, format="wav")

            try:
                os.remove(temp_mp3)
            except Exception:
                pass

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ edge-tts audio saved: {output_path}")
                return True
            return False

        except ImportError:
            print("⚠️ edge-tts not installed, falling back to gTTS...")
            return self._generate_with_gtts(text, output_path, language)
        except Exception as e:
            print(f"❌ edge-tts failed: {e}")
            traceback.print_exc()
            print("⚠️ Falling back to gTTS...")
            return self._generate_with_gtts(text, output_path, language)

    def _generate_with_gtts(self, text: str, output_path: str, language: str = 'vi') -> bool:
        """Generate audio using gTTS (Google Text-to-Speech) with language support"""
        try:
            print(f"🎧 Generating audio with gTTS ({language})...")
            
            # Import required modules
            from gtts import gTTS
            from pydub import AudioSegment
            import tempfile
            
            print(f"  📝 Text length: {len(text)} characters")
            print(f"  🌐 Language: {language}")
            
            # Validate text
            if not text or len(text.strip()) < 3:
                print("  ❌ Text too short for TTS")
                return False
            
            # Validate language
            if language not in self.SUPPORTED_LANGUAGES:
                print(f"  ⚠️  Language {language} not supported, using English")
                language = 'en'
            
            # Tạo gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            print("  ✅ gTTS object created")
            
            # Tạo temp file an toàn
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_mp3 = temp_file.name
            
            print(f"  📋 Saving to temp MP3: {temp_mp3}")
            tts.save(temp_mp3)
            
            # Kiểm tra file MP3 đã tạo thành công
            if not os.path.exists(temp_mp3):
                print("  ❌ MP3 file not created")
                return False
                
            file_size = os.path.getsize(temp_mp3)
            print(f"  ✅ MP3 created, size: {file_size} bytes")
            
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(output_path, format="wav")
            print(f"  ✅ Converted to WAV: {output_path}")
            
            # Kiểm tra file WAV
            if os.path.exists(output_path):
                wav_size = os.path.getsize(output_path)
                print(f"  ✅ WAV created, size: {wav_size} bytes")
            else:
                print("  ❌ WAV file not created")
                return False
            
            # Clean up temp file
            try:
                os.remove(temp_mp3)
                print(f"  🧹 Cleaned up temp file")
            except:
                print(f"  ⚠️  Could not clean up temp file: {temp_mp3}")
            
            print(f"✅ gTTS audio saved successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ gTTS failed: {e}")
            traceback.print_exc()
            return False
    

    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean and prepare text for TTS generation"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        clean_text = ' '.join(text.split())
        
        # Remove or replace problematic characters
        clean_text = clean_text.replace('\n', '. ')
        clean_text = clean_text.replace('\r', ' ')
        clean_text = clean_text.replace('\t', ' ')
        
        # Ensure sentences end with proper punctuation for better TTS
        clean_text = clean_text.strip()
        if clean_text and clean_text[-1] not in '.!?':
            clean_text += '.'
        
        return clean_text
    
    def get_audio_url(self, presentation_id: str, slide_index: int) -> str:
        """Generate the URL path for accessing the audio file"""
        return f"/static/audio/{presentation_id}/slide_{slide_index}.wav"
    
    def get_audio_file_path(self, presentation_id: str, slide_index: int, static_folder: str) -> str:
        """Generate the full file system path for the audio file"""
        audio_dir = os.path.join(static_folder, "audio", presentation_id)
        return os.path.join(audio_dir, f"slide_{slide_index}.wav")

    def merge_audio_files(self, audio_paths: list, output_path: str) -> bool:
        """Merge multiple audio files into one"""
        try:
            from moviepy.editor import concatenate_audioclips, AudioFileClip
            
            clips = []
            for path in audio_paths:
                if os.path.exists(path):
                    try:
                        clips.append(AudioFileClip(path))
                    except Exception as e:
                        print(f"⚠️ Error loading clip {path}: {e}")
            
            if not clips:
                print("❌ No valid clips to merge")
                return False
                
            final_clip = concatenate_audioclips(clips)
            final_clip.write_audiofile(output_path, logger=None)
            
            # Close clips to release file handles
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return True
        except ImportError:
            print("❌ moviepy not available for audio merging")
            return False
        except Exception as e:
            print(f"❌ Error merging audio: {e}")
            traceback.print_exc()
            return False
    
    def cleanup_presentation_audio(self, presentation_id: str, static_folder: str):
        """Clean up all audio files for a presentation"""
        try:
            audio_dir = os.path.join(static_folder, "audio", presentation_id)
            if os.path.exists(audio_dir):
                import shutil
                shutil.rmtree(audio_dir)
                print(f"🧹 Cleaned up audio files for presentation {presentation_id}")
        except Exception as e:
            print(f"⚠️  Failed to cleanup audio files: {e}")
    
    def close(self):
        """Clean up resources"""
        try:
            if self.vieneu_engine and hasattr(self.vieneu_engine, 'close'):
                self.vieneu_engine.close()
                print("🧹 VieNeu-TTS engine closed")
        except Exception as e:
            print(f"⚠️  Error closing VieNeu engine: {e}")


# Global instance
_audio_service = None

def get_audio_service(force_gtts=False) -> AudioService:
    """Get or create the global AudioService instance
    
    Args:
        force_gtts: If True, skip VieNeu-TTS and use gTTS directly (recommended for stability)
    """
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService(force_gtts=force_gtts)
    return _audio_service