"""
Script để chạy tất cả tests
"""
import unittest
import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Chạy tất cả test cases"""
    # Tìm tất cả test files
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests từ các test files
    test_files = [
        'tests.test_presentation_reader',
        'tests.test_api_routes',
        'tests.test_integration',
        'tests.test_file_validation',
    ]
    
    for test_file in test_files:
        try:
            tests = loader.loadTestsFromName(test_file)
            suite.addTests(tests)
            print(f"[OK] Loaded tests from {test_file}")
        except Exception as e:
            print(f"[WARN] Could not load {test_file}: {e}")
    
    # Chạy tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Tóm tắt kết quả
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)

