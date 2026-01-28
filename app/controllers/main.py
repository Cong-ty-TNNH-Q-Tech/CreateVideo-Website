from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('presentation.html')

@main_bp.route('/old')
def old_home():
    """Old SadTalker demo page"""
    return render_template('index.html')
