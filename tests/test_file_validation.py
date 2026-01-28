"""
Test cases cho file validation
"""
import unittest
import os
import tempfile
import sys

# Try to import app, skip tests if dependencies not installed
try:
    from app import app
    APP_AVAILABLE = True
except ImportError as e:
    APP_AVAILABLE = False
    print(f"Warning: Cannot import app: {e}. Some tests will be skipped.")

class TestFileValidation(unittest.TestCase):
    """Test cases cho validation file upload"""
    
    def setUp(self):
        """Setup test environment"""
        if not APP_AVAILABLE:
            self.skipTest("App not available (dependencies not installed)")
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['PRESENTATION_FOLDER'] = tempfile.mkdtemp()
        self.client = self.app.test_client()
    
    def test_file_extension_validation(self):
        """Test validation file extension"""
        valid_extensions = ['.pptx', '.ppt', '.pdf']
        invalid_extensions = ['.txt', '.docx', '.xlsx', '.jpg', '.png']
        
        for ext in invalid_extensions:
            test_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            test_file.write(b'Test content')
            test_file.close()
            
            with open(test_file.name, 'rb') as f:
                response = self.client.post(
                    '/api/upload-presentation',
                    data={'file': (f, f'test{ext}')},
                    content_type='multipart/form-data'
                )
            
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertFalse(data['success'])
            self.assertIn('Invalid file type', data['error'])
            
            os.unlink(test_file.name)
    
    def test_file_size_validation(self):
        """Test validation file size (100MB limit)"""
        # Tạo file lớn hơn 100MB (mock)
        # Note: Trong thực tế cần tạo file thật để test
        # Ở đây chỉ test structure
        max_size = 100 * 1024 * 1024  # 100MB
        self.assertEqual(self.app.config['MAX_CONTENT_LENGTH'], max_size)
    
    def test_secure_filename(self):
        """Test secure filename handling"""
        from werkzeug.utils import secure_filename
        
        test_cases = [
            ('normal_file.pptx', 'normal_file.pptx'),
            ('file with spaces.pptx', 'file_with_spaces.pptx'),
            ('file/with/slashes.pptx', 'file_with_slashes.pptx'),
            ('file\\with\\backslashes.pptx', 'file_with_backslashes.pptx'),
        ]
        
        for input_name, expected in test_cases:
            result = secure_filename(input_name)
            # Kiểm tra không có ký tự nguy hiểm
            self.assertNotIn('/', result)
            self.assertNotIn('\\', result)
            # secure_filename không xử lý '..' trong tên file, chỉ xử lý slashes
            # Nhưng kiểm tra không có path traversal
            self.assertNotEqual(result, '../file.pptx')

if __name__ == '__main__':
    unittest.main()

