import requests
import time

def check_preview():
    url = "http://127.0.0.1:5000/api/preview-voice"
    # Minimize data to test the parsing logic
    # Sending as multipart/form-data via files parameter (even for text fields, requests handles it)
    data = {
        'text': 'Test voice preview',
        'voice_id': 'default' 
    }
    
    # We use 'data' for non-file fields in multipart request with requests lib
    # but to force multipart, we might need a file or just rely on requests.
    # Actually requests.post(url, data=data) sends x-www-form-urlencoded by default?
    # No, to send multipart without files, we can do:
    # files = {'dummy': (None, 'dummy')} 
    # But let's try sending just data. The backend logic I wrote handles request.form.
    
    try:
        print("Sending request...")
        # To simulate the browser's FormData, we should probably send multipart.
        # Browser fetch with FormData sends multipart/form-data.
        # Let's send a dummy file to ensure it's multipart.
        files = {
            'text': (None, 'Test voice preview'),
            'voice_id': (None, 'Binh') # Use a valid voice ID if possible, or any string
        }
        
        response = requests.post(url, files=files) 
        
        print(f"Status Code: {response.status_code}")
        # 415 is what we want to avoid.
        # 500 might happen if generation fails, but that's a different error.
        # 200 is best.
        if response.status_code != 415:
             print("✅ Success: Not 415")
        else:
             print("❌ Failed: 415 Unsupported Media Type")
             
        print(f"Response: {response.text[:200]}...")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    time.sleep(2) # Wait for server
    check_preview()
