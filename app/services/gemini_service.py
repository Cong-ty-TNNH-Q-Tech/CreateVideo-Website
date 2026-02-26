"""
Service to interact with Google Gemini API for generating presentation scripts.
Supports multiple API keys with automatic round-robin rotation on quota/rate-limit errors.
"""
import os
import threading
from google import genai
from typing import Optional, List

# Errors that trigger key rotation (quota exhausted, rate limit, invalid key, etc.)
_ROTATE_KEYWORDS = (
    'quota', 'rate', '429', 'resource_exhausted', 'resourceexhausted',
    'api_key_invalid', 'permission_denied', 'invalid api key',
    'too many requests', 'limit exceeded',
)

def _is_rotatable_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in _ROTATE_KEYWORDS)


class GeminiService:
    """Service to interact with Gemini API with multi-key rotation support."""

    def __init__(self, api_keys: Optional[List[str]] = None, api_key: Optional[str] = None):
        """
        Initialize Gemini service.

        Args:
            api_keys: List of Gemini API keys for rotation.
            api_key:  Single key fallback (legacy).
                      If neither is given, reads GEMINI_API_KEYS (comma-separated)
                      then GEMINI_API_KEY from environment.
        """
        # Build key list
        if api_keys:
            keys = [k.strip() for k in api_keys if k and k.strip()]
        else:
            # Try GEMINI_API_KEYS (comma-separated) first
            multi = os.getenv('GEMINI_API_KEYS', '')
            keys = [k.strip() for k in multi.split(',') if k.strip()]
            if not keys:
                # Fallback to single key
                single = api_key or os.getenv('GEMINI_API_KEY', '')
                if single.strip():
                    keys = [single.strip()]

        self._keys: List[str] = keys
        self._current_idx: int = 0
        self._lock = threading.Lock()

        if not self._keys:
            print("⚠️  Warning: No Gemini API key configured. Set GEMINI_API_KEYS or GEMINI_API_KEY.")
            self._client = None
        else:
            print(f"✅ GeminiService initialized with {len(self._keys)} API key(s).")
            self._client = genai.Client(api_key=self._keys[0])

        # Generation config for TTS-friendly output
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        self.model_name = 'gemini-2.5-flash'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> genai.Client:
        if not self._keys:
            raise ValueError("Gemini API key is not configured.")
        return self._client

    def _rotate(self) -> bool:
        """Rotate to the next available key. Returns True if a new key was selected."""
        with self._lock:
            if len(self._keys) <= 1:
                return False
            next_idx = (self._current_idx + 1) % len(self._keys)
            if next_idx == self._current_idx:
                return False
            self._current_idx = next_idx
            new_key = self._keys[self._current_idx]
            self._client = genai.Client(api_key=new_key)
            print(f"🔄 Gemini key rotated → key index {self._current_idx} (****{new_key[-4:]})")
            return True

    def _call_with_rotation(self, fn):
        """
        Execute fn(client) and auto-rotate keys on quota/rate errors.
        Tries every key once before re-raising.
        """
        if not self._keys:
            raise ValueError("Gemini API key is not configured.")

        attempts = len(self._keys)
        last_exc = None
        for attempt in range(attempts):
            try:
                return fn(self._client)
            except Exception as exc:
                last_exc = exc
                key_hint = self._keys[self._current_idx][-4:]
                if _is_rotatable_error(exc):
                    print(f"⚠️  Gemini key ****{key_hint} hit quota/rate error (attempt {attempt + 1}/{attempts}): {exc}")
                    if not self._rotate():
                        break  # only 1 key, no point retrying
                else:
                    raise  # non-rotatable error → propagate immediately
        raise last_exc

    # ------------------------------------------------------------------
    # Public API (unchanged signatures)
    # ------------------------------------------------------------------

    def generate_script(self, slide_text: str, language: str = 'vi') -> str:
        """Generate a speech script from slide text."""
        if not self._keys:
            raise ValueError("Gemini API key is not configured.")

        if not slide_text or not slide_text.strip():
            return "Slide này không có nội dung, vui lòng nhập nội dung để tạo kịch bản."

        prompt = f"""
        Act as a professional presenter and speaker.
        Rewrite the following slide content into a natural, engaging speech script suitable for Text-to-Speech (TTS).
        
        Input Text:
        "{slide_text}"
        
        Requirements:
        1. Language: Detect the main language of the Input Text and write the Generated Script in the SAME language.
        2. Tone: Professional, engaging, and clear.
        3. Format: PLAIN TEXT ONLY. Do NOT use Markdown, lists, bullet points, asterisks (*), hashtags (#), or emojis. TTS engines do not read these well.
        4. Structure: Write in full sentences/paragraphs as if you are speaking to an audience.
        5. Content: Do not just read the text. Explain and expand on the points naturally.
        6. Length: Keep it concise and appropriate for the amount of content (approx. 1-2 minutes max).
        
        Generated Script:
        """

        def _call(client):
            return client.models.generate_content(
                model=self.model_name, contents=prompt, config=self.generation_config
            ).text.strip()

        try:
            return self._call_with_rotation(_call)
        except Exception as e:
            print(f"❌ Gemini generate_script failed: {e}")
            raise Exception(f"Gemini API Error: {str(e)}")

    def enhance_text(self, current_text: str, instruction: str) -> str:
        """Enhance the existing script based on user instruction."""
        if not self._keys:
            raise ValueError("Gemini API key is not configured.")

        prompt = f"""
        Act as a professional editor.
        Update the following speech script based on the instruction.
        
        Current Script:
        "{current_text}"
        
        Instruction:
        "{instruction}"
        
        Requirements:
        1. Keep it as PLAIN TEXT (no markdown/emojis).
        2. Maintain a professional speech tone.
        3. Make it suitable for TTS.
        
        Updated Script:
        """

        def _call(client):
            return client.models.generate_content(
                model=self.model_name, contents=prompt, config=self.generation_config
            ).text.strip()

        try:
            return self._call_with_rotation(_call)
        except Exception as e:
            raise Exception(f"Gemini enhancement error: {str(e)}")

    def regenerate_text(self, slide_content: str, current_text: str, feedback: str) -> str:
        """Regenerate the script with feedback."""
        if not self._keys:
            raise ValueError("Gemini API key is not configured.")

        prompt = f"""
        Act as a professional presenter.
        Regenerate the speech script for the slide content, taking into account the user's feedback.
        
        Slide Content:
        "{slide_content}"
        
        Current Script:
        "{current_text}"
        
        User Feedback:
        "{feedback}"
        
        Requirements:
        1. Address the feedback specifically.
        2. Format: PLAIN TEXT ONLY (no markdown/emojis).
        3. Tone: Professional and natural for speech.
        
        New Script:
        """

        def _call(client):
            return client.models.generate_content(
                model=self.model_name, contents=prompt, config=self.generation_config
            ).text.strip()

        try:
            return self._call_with_rotation(_call)
        except Exception as e:
            raise Exception(f"Gemini regeneration error: {str(e)}")

    # ------------------------------------------------------------------
    # Status info
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return current key pool status (for debugging)."""
        return {
            'total_keys': len(self._keys),
            'current_key_index': self._current_idx,
            'current_key_hint': f"****{self._keys[self._current_idx][-4:]}" if self._keys else None,
        }
