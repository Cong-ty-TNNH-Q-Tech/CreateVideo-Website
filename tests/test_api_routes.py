"""
Test cases cho API routes của presentation
"""
import unittest
import os
import json
import tempfile
from pathlib import Path

# Try to import app, skip tests if dependencies not installed
try:
    from flask import Flask
    from app import app, presentations, save_presentations, load_presentations
    APP_AVAILABLE = True
except ImportError as e:
    APP_AVAILABLE = False
    print(f"Warning: Cannot import app: {e}. Some tests will be skipped.")

class TestAPIRoutes(unittest.TestCase):
    """Test cases cho API routes"""
    
    def setUp(self):
        """Setup test client"""
        if not APP_AVAILABLE:
            self.skipTest("App not available (dependencies not installed)")
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['PRESENTATION_FOLDER'] = tempfile.mkdtemp()
        self.app.config['DATA_FOLDER'] = tempfile.mkdtemp()
        self.client = self.app.test_client()
        
        # Clear presentations
        global presentations
        presentations.clear()
    
    def tearDown(self):
        """Cleanup after tests"""
        global presentations
        presentations.clear()
    
    def test_upload_presentation_no_file(self):
        """Test upload không có file"""
        response = self.client.post('/api/upload-presentation')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('No file provided', data['error'])
    
    def test_upload_presentation_empty_filename(self):
        """Test upload với filename rỗng"""
        response = self.client.post(
            '/api/upload-presentation',
            data={'file': (None, '')}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_upload_presentation_invalid_file_type(self):
        """Test upload file type không hợp lệ"""
        # Tạo file test
        test_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        test_file.write(b'Test content')
        test_file.close()
        
        with open(test_file.name, 'rb') as f:
            response = self.client.post(
                '/api/upload-presentation',
                data={'file': (f, 'test.txt')},
                content_type='multipart/form-data'
            )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Invalid file type', data['error'])
        
        os.unlink(test_file.name)
    
    def test_get_presentation_not_found(self):
        """Test get presentation không tồn tại"""
        response = self.client.get('/api/presentation/nonexistent-id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_get_slides_not_found(self):
        """Test get slides của presentation không tồn tại"""
        response = self.client.get('/api/presentation/nonexistent-id/slides')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_get_slide_not_found(self):
        """Test get slide không tồn tại"""
        # Tạo presentation giả
        global presentations
        presentations['test-id'] = {
            'id': 'test-id',
            'filename': 'test.pptx',
            'slides': [
                {'slide_num': 1, 'content': 'Test'}
            ]
        }
        
        # Test slide không tồn tại
        response = self.client.get('/api/presentation/test-id/slide/999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_get_slide_success(self):
        """Test get slide thành công"""
        # Tạo presentation giả
        global presentations
        presentations['test-id'] = {
            'id': 'test-id',
            'filename': 'test.pptx',
            'slides': [
                {
                    'slide_num': 1,
                    'content': 'Test content',
                    'notes': 'Test notes',
                    'total_slides': 1
                }
            ]
        }
        
        response = self.client.get('/api/presentation/test-id/slide/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['slide']['slide_num'], 1)
        self.assertEqual(data['slide']['content'], 'Test content')

if __name__ == '__main__':
    unittest.main()

