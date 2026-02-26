from app.services.gemini_service import GeminiService
import os

_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Lazy-load GeminiService singleton with multi-key support.

    Reads keys from (in priority order):
      1. GEMINI_API_KEYS  — comma-separated list, e.g. "key1,key2,key3"
      2. GEMINI_API_KEY   — single key (legacy)
    """
    global _gemini_service
    if _gemini_service is None:
        try:
            _gemini_service = GeminiService()  # reads env vars internally
        except Exception as e:
            print(f"Warning: Could not initialize Gemini service: {e}")
            print("Please set GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY environment variable")
    return _gemini_service


def reset_gemini_service():
    """Force re-initialization (useful after env var changes)."""
    global _gemini_service
    _gemini_service = None
