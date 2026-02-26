import os

class Config:
    UPLOAD_FOLDER = 'static/uploads'
    RESULT_FOLDER = 'static/results'
    PRESENTATION_FOLDER = 'static/uploads/presentations'
    DATA_FOLDER = 'data'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

    # Single key (legacy) — still supported
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Multi-key pool (comma-separated). Takes priority over GEMINI_API_KEY.
    # Example: GEMINI_API_KEYS=key1,key2,key3
    GEMINI_API_KEYS = os.environ.get('GEMINI_API_KEYS', '')

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.RESULT_FOLDER, exist_ok=True)
        os.makedirs(Config.PRESENTATION_FOLDER, exist_ok=True)
        os.makedirs(Config.DATA_FOLDER, exist_ok=True)
