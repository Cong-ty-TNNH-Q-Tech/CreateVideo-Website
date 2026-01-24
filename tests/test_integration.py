"""
Integration tests - Test toàn bộ flow từ upload đến đọc slides
"""
import unittest
import os
import tempfile
import json

# Try to import app, skip tests if dependencies not installed
try:
    from flask import Flask
    from app import app, presentations
    APP_AVAILABLE = True
except ImportError as e:
    APP_AVAILABLE = False
    print(f"Warning: Cannot import app: {e}. Some tests will be skipped.")

class TestIntegration(unittest.TestCase):
    """Integration tests cho toàn bộ workflow"""
    
    def setUp(self):
        """Setup test environment"""
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
        """Cleanup"""
        global presentations
        presentations.clear()
    
    def test_full_workflow_mock(self):
        """Test full workflow với mock data"""
        # 1. Upload presentation (mock)
        # 2. Get presentation info
        # 3. Get all slides
        # 4. Get specific slide
        
        # Tạo presentation mock
        pres_id = 'test-pres-123'
        global presentations
        presentations[pres_id] = {
            'id': pres_id,
            'filename': 'test.pptx',
            'type': '.pptx',
            'slides': [
                {
                    'slide_num': 1,
                    'content': 'Slide 1 content',
                    'notes': 'Notes 1',
                    'total_slides': 2,
                    'generated_text': '',
                    'edited_text': '',
                    'status': 'pending'
                },
                {
                    'slide_num': 2,
                    'content': 'Slide 2 content',
                    'notes': '',
                    'total_slides': 2,
                    'generated_text': '',
                    'edited_text': '',
                    'status': 'pending'
                }
            ]
        }
        
        # Test get presentation
        response = self.client.get(f'/api/presentation/{pres_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['presentation']['id'], pres_id)
        self.assertEqual(len(data['presentation']['slides']), 2)
        
        # Test get all slides
        response = self.client.get(f'/api/presentation/{pres_id}/slides')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['slides']), 2)
        
        # Test get slide 1
        response = self.client.get(f'/api/presentation/{pres_id}/slide/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['slide']['slide_num'], 1)
        self.assertEqual(data['slide']['content'], 'Slide 1 content')
        
        # Test get slide 2
        response = self.client.get(f'/api/presentation/{pres_id}/slide/2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['slide']['slide_num'], 2)

if __name__ == '__main__':
    unittest.main()

