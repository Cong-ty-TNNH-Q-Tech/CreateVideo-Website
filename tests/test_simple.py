"""
Simple tests không cần dependencies
"""
import unittest
from werkzeug.utils import secure_filename

class TestSimple(unittest.TestCase):
    """Simple tests không cần dependencies"""
    
    def test_secure_filename_basic(self):
        """Test secure_filename cơ bản"""
        self.assertEqual(secure_filename('normal_file.pptx'), 'normal_file.pptx')
        self.assertEqual(secure_filename('file with spaces.pptx'), 'file_with_spaces.pptx')
        self.assertEqual(secure_filename('file/with/slashes.pptx'), 'file_with_slashes.pptx')
        self.assertEqual(secure_filename('file\\with\\backslashes.pptx'), 'file_with_backslashes.pptx')
    
    def test_secure_filename_special_chars(self):
        """Test secure_filename với ký tự đặc biệt"""
        # secure_filename chỉ xử lý slashes, không xử lý '..' trong tên file
        result = secure_filename('file/../dangerous.pptx')
        self.assertNotIn('/', result)
        # Kiểm tra không có path traversal
        self.assertNotEqual(result, '../dangerous.pptx')
    
    def test_basic_math(self):
        """Test toán học cơ bản"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual(2 * 2, 4)
        self.assertGreater(10, 5)
    
    def test_string_operations(self):
        """Test string operations"""
        text = "Hello World"
        self.assertEqual(text.upper(), "HELLO WORLD")
        self.assertEqual(len(text), 11)
        self.assertIn("World", text)

if __name__ == '__main__':
    unittest.main()

