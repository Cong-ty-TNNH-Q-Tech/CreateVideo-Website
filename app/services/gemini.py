from app.services.gemini_service import GeminiService
import os

_gemini_service = None

def get_gemini_service():
    """Lazy load Gemini service"""
    global _gemini_service
    if _gemini_service is None:
        try:
            _gemini_service = GeminiService()
        except Exception as e:
            print(f"Warning: Could not initialize Gemini service: {e}")
            print("Please set GEMINI_API_KEY environment variable")
    return _gemini_service
