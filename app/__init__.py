# -*- coding: utf-8 -*-
import os
import sys

# Ensure UTF-8 encoding on Windows for all modules
if sys.platform == 'win32':
    # Set environment variable for UTF-8 encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8:replace'
    
    # Instead of wrapping stdout/stderr (which can break Flask debugger),
    # we'll just set the default encoding at import time
    # This approach is less invasive and safer for Flask
    import locale
    try:
        # Try to set console to UTF-8 mode if possible
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # If reconfigure fails, just continue - environment variable will help
        pass

from flask import Flask
from config import Config
from app.models.presentation_model import PresentationModel
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    
    # Initialize storage directories
    Config.init_app(app)
    
    # Initialize Model
    app.presentation_model = PresentationModel(app.config['DATA_FOLDER'])
    
    # Register Blueprints
    from app.controllers.main import main_bp
    from app.controllers.presentation import presentation_bp
    from app.controllers.generation import generation_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(presentation_bp)
    app.register_blueprint(generation_bp)
    
    return app
