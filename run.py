# -*- coding: utf-8 -*-
import os
import sys

# Fix Windows console encoding issues with Unicode (emojis, Vietnamese text)
if sys.platform == 'win32':
    # Set environment variable for UTF-8 encoding with error replacement
    os.environ['PYTHONIOENCODING'] = 'utf-8:replace'
    
    # Use reconfigure instead of wrapping to avoid Flask debugger issues
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # Silently continue if reconfigure fails
        pass

from app import create_app
from download_models import ensure_models

# Check and download SadTalker models if needed
print("Initializing VideoTeaching application...")
if not ensure_models():
    print("\n[ERROR] Failed to ensure SadTalker models are available.")
    print("Please run 'python download_models.py' manually or check your internet connection.")
    sys.exit(1)

print("\n" + "="*60)
print("Starting Flask application...")
print("="*60 + "\n")

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
