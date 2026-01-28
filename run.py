from app import create_app
from download_models import ensure_models
import sys

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
