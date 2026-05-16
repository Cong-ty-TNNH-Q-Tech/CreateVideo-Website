"""
OmniVoice Service for High-Quality Multilingual Voice Cloning

Wraps k2-fsa/OmniVoice — a zero-shot TTS model supporting 600+ languages.
Used as the primary engine for voice_type='clone' in AudioService.

Reference: https://github.com/k2-fsa/OmniVoice
"""

import os
import threading
import traceback
from typing import Optional

OMNIVOICE_AVAILABLE = False
OmniVoiceClass = None


def _try_import():
    """Attempt to import OmniVoice at module load time."""
    global OMNIVOICE_AVAILABLE, OmniVoiceClass
    try:
        from omnivoice import OmniVoice
        OmniVoiceClass = OmniVoice
        OMNIVOICE_AVAILABLE = True
    except ImportError:
        OMNIVOICE_AVAILABLE = False


_try_import()


class OmniVoiceService:
    """
    Singleton service wrapping the OmniVoice TTS model.

    Supports:
    - Voice cloning: clone a voice from a 3–10 s reference audio clip.
    - Voice design: describe a voice via text attributes (no reference needed).
    - Auto voice: let the model choose a voice automatically.
    """

    def __init__(self, device: Optional[str] = None, dtype_fp16: bool = True):
        """
        Args:
            device: 'cuda:0', 'cpu', 'mps', or None (auto-detect).
            dtype_fp16: Use float16 for GPU inference (faster). Ignored on CPU.
        """
        self.model = None
        self.available = False
        self._lock = threading.Lock()
        self._device = device
        self._dtype_fp16 = dtype_fp16
        self._init_model()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _auto_detect_device(self) -> str:
        """Return the best available device string."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda:0"
        except Exception:
            pass
        return "cpu"

    def _init_model(self):
        """Load the OmniVoice model. Called once at construction time."""
        if not OMNIVOICE_AVAILABLE or OmniVoiceClass is None:
            print("⚠️  OmniVoice not installed — voice cloning will fall back to VieNeu/edge-tts")
            print("    Install with: pip install omnivoice")
            return

        try:
            import torch
            device = self._device or self._auto_detect_device()
            dtype = torch.float16 if (self._dtype_fp16 and "cuda" in device) else torch.float32

            print(f"🚀 Initializing OmniVoice model (device={device}, dtype={dtype})...")
            self.model = OmniVoiceClass.from_pretrained(
                "k2-fsa/OmniVoice",
                device_map=device,
                dtype=dtype,
            )
            self.available = True
            print("✅ OmniVoice model ready")

        except Exception as e:
            print(f"❌ OmniVoice initialization failed: {e}")
            traceback.print_exc()
            self.available = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clone_voice(
        self,
        text: str,
        ref_audio: str,
        ref_text: Optional[str] = None,
        output_path: str = None,
        speed: float = 1.0,
        num_step: int = 32,
    ) -> bool:
        """
        Generate speech by cloning a voice from a reference audio clip.

        Args:
            text:        The text to synthesise.
            ref_audio:   Path to the reference audio file (3–10 s WAV recommended).
            ref_text:    Transcript of the reference audio (optional — improves
                         alignment; OmniVoice auto-transcribes via Whisper if omitted).
            output_path: Where to save the output WAV file.
            speed:       Speaking rate (1.0 = normal, >1 faster, <1 slower).
            num_step:    Diffusion steps (32 = quality, 16 = faster).

        Returns:
            True on success, False on failure.
        """
        if not self.available or self.model is None:
            print("❌ OmniVoice not available for voice cloning")
            return False

        if not ref_audio or not os.path.exists(ref_audio):
            print(f"❌ Reference audio not found: {ref_audio}")
            return False

        if not output_path:
            print("❌ output_path is required")
            return False

        try:
            import soundfile as sf
            print(f"🎤 OmniVoice: cloning voice from '{os.path.basename(ref_audio)}'...")
            print(f"   ref_text={'<auto-whisper>' if not ref_text else repr(ref_text[:60])}")
            print(f"   text length={len(text)}, speed={speed}, steps={num_step}")

            with self._lock:
                kwargs = dict(
                    text=text,
                    ref_audio=ref_audio,
                    speed=speed,
                    num_step=num_step,
                )
                # Pass ref_text only when non-empty; None triggers Whisper ASR inside OmniVoice
                if ref_text and ref_text.strip():
                    kwargs["ref_text"] = ref_text.strip()

                audio_list = self.model.generate(**kwargs)

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            sf.write(output_path, audio_list[0], samplerate=24000)
            print(f"✅ OmniVoice cloned audio saved: {output_path}")
            return True

        except Exception as e:
            print(f"❌ OmniVoice clone_voice failed: {e}")
            traceback.print_exc()
            return False

    def generate(
        self,
        text: str,
        output_path: str,
        instruct: Optional[str] = None,
        speed: float = 1.0,
        num_step: int = 32,
    ) -> bool:
        """
        Generate speech without a reference audio (auto voice or voice design).

        Args:
            text:        Text to synthesise.
            output_path: Where to save the output WAV file.
            instruct:    Voice design attributes e.g. "female, british accent, low pitch".
                         If None, the model selects a voice automatically.
            speed:       Speaking rate.
            num_step:    Diffusion steps.

        Returns:
            True on success, False on failure.
        """
        if not self.available or self.model is None:
            print("❌ OmniVoice not available")
            return False

        try:
            import soundfile as sf
            mode = f"voice design ({instruct})" if instruct else "auto voice"
            print(f"🎤 OmniVoice: generating [{mode}], text length={len(text)}")

            with self._lock:
                kwargs = dict(text=text, speed=speed, num_step=num_step)
                if instruct:
                    kwargs["instruct"] = instruct
                audio_list = self.model.generate(**kwargs)

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            sf.write(output_path, audio_list[0], samplerate=24000)
            print(f"✅ OmniVoice audio saved: {output_path}")
            return True

        except Exception as e:
            print(f"❌ OmniVoice generate failed: {e}")
            traceback.print_exc()
            return False

    def is_available(self) -> bool:
        """Return True if the model is loaded and ready."""
        return self.available and self.model is not None


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------

_omnivoice_service: Optional[OmniVoiceService] = None
_ov_init_lock = threading.Lock()


def get_omnivoice_service(
    device: Optional[str] = None,
    dtype_fp16: bool = True,
) -> OmniVoiceService:
    """
    Return (or lazily create) the global OmniVoiceService singleton.

    Args:
        device:      Force a device string, e.g. 'cpu', 'cuda:0'. None = auto.
        dtype_fp16:  Use float16 on CUDA (faster). Ignored on CPU.
    """
    global _omnivoice_service
    if _omnivoice_service is None:
        with _ov_init_lock:
            if _omnivoice_service is None:  # double-checked locking
                _omnivoice_service = OmniVoiceService(device=device, dtype_fp16=dtype_fp16)
    return _omnivoice_service
