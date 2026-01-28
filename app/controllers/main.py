from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('presentation.html')

@main_bp.route('/test/sadtalker')
def test_sadtalker():
    """Test page for SadTalker video generation"""
    return render_template('test_sadtalker.html')

@main_bp.route('/test/tts')
def test_tts():
    """Test page for VieNeu-TTS voice synthesis"""
    return render_template('test_tts.html')
