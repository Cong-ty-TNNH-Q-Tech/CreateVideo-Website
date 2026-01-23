import sys
print(f"Python: {sys.executable}")
print(f"Path: {sys.path}")
try:
    import cv2
    print(f"CV2 Version: {cv2.__version__}")
except ImportError as e:
    print(f"ImportError: {e}")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {e}")
except Exception as e:
    print(f"Error: {e}")
