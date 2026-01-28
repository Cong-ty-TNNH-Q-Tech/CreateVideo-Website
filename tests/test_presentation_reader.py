"""
Test cases cho PresentationReader
"""
import unittest
import os
import tempfile
from pathlib import Path

# Try to import, skip tests if dependencies not installed
try:
    from app.utils.presentation_reader import PresentationReader
    READER_AVAILABLE = True
except ImportError as e:
    READER_AVAILABLE = False
    print(f"Warning: Cannot import PresentationReader: {e}. Some tests will be skipped.")

class TestPresentationReader(unittest.TestCase):
    """Test cases cho PresentationReader"""
    
    def setUp(self):
        """Setup test environment"""
        if not READER_AVAILABLE:
            self.skipTest("PresentationReader not available (dependencies not installed)")
        self.reader = PresentationReader()
        self.test_dir = tempfile.mkdtemp()
    
    def test_read_pptx_file_not_found(self):
        """Test đọc file PPTX không tồn tại"""
        with self.assertRaises(FileNotFoundError):
            self.reader.extract_text_from_file("nonexistent.pptx")
    
    def test_read_unsupported_file_type(self):
        """Test đọc file type không hỗ trợ"""
        # Tạo file test giả
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ValueError) as context:
            self.reader.extract_text_from_file(test_file)
        
        self.assertIn("Unsupported file type", str(context.exception))
    
    def test_read_pdf_basic(self):
        """Test đọc file PDF cơ bản"""
        # Tạo file PDF test đơn giản
        # Note: Cần có file PDF thật để test, hoặc tạo PDF programmatically
        # Ở đây chỉ test structure
        pass
    
    def test_read_pptx_structure(self):
        """Test structure của kết quả đọc PPTX"""
        # Test với file PPTX thật (nếu có)
        # Hoặc mock data
        pass
    
    def test_extract_text_from_file_auto_detect(self):
        """Test tự động detect file type"""
        # Test với các extension khác nhau
        test_cases = [
            (".pptx", True),
            (".ppt", True),
            (".pdf", True),
            (".txt", False),
            (".docx", False),
        ]
        
        for ext, should_support in test_cases:
            if should_support:
                # Chỉ test validation, không test đọc thật
                pass

if __name__ == '__main__':
    unittest.main()

