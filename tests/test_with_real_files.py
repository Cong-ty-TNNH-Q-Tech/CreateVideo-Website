"""
Test với file PPT/PDF thật (nếu có)
Cần có file test trong thư mục tests/test_files/
"""
import unittest
import os
from pathlib import Path
from app.utils.presentation_reader import PresentationReader

class TestWithRealFiles(unittest.TestCase):
    """Test với file thật (nếu có)"""
    
    def setUp(self):
        """Setup"""
        self.reader = PresentationReader()
        self.test_files_dir = Path(__file__).parent / 'test_files'
    
    def test_read_real_pptx(self):
        """Test đọc file PPTX thật"""
        pptx_file = self.test_files_dir / 'test.pptx'
        
        if not pptx_file.exists():
            self.skipTest(f"Test file not found: {pptx_file}")
        
        slides = self.reader.read_pptx(str(pptx_file))
        
        # Assertions
        self.assertIsInstance(slides, list)
        self.assertGreater(len(slides), 0)
        
        # Kiểm tra structure
        for slide in slides:
            self.assertIn('slide_num', slide)
            self.assertIn('content', slide)
            self.assertIn('total_slides', slide)
            self.assertIsInstance(slide['slide_num'], int)
            self.assertIsInstance(slide['content'], str)
    
    def test_read_real_pdf(self):
        """Test đọc file PDF thật"""
        pdf_file = self.test_files_dir / 'test.pdf'
        
        if not pdf_file.exists():
            self.skipTest(f"Test file not found: {pdf_file}")
        
        pages = self.reader.read_pdf(str(pdf_file))
        
        # Assertions
        self.assertIsInstance(pages, list)
        self.assertGreater(len(pages), 0)
        
        # Kiểm tra structure
        for page in pages:
            self.assertIn('slide_num', page)
            self.assertIn('content', page)
            self.assertIn('total_slides', page)
            self.assertIsInstance(page['slide_num'], int)
            self.assertIsInstance(page['content'], str)
    
    def test_extract_text_from_real_file(self):
        """Test extract text từ file thật"""
        # Test với PPTX
        pptx_file = self.test_files_dir / 'test.pptx'
        if pptx_file.exists():
            slides = self.reader.extract_text_from_file(str(pptx_file))
            self.assertIsInstance(slides, list)
            self.assertGreater(len(slides), 0)
        
        # Test với PDF
        pdf_file = self.test_files_dir / 'test.pdf'
        if pdf_file.exists():
            pages = self.reader.extract_text_from_file(str(pdf_file))
            self.assertIsInstance(pages, list)
            self.assertGreater(len(pages), 0)

if __name__ == '__main__':
    unittest.main()

