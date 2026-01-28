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
