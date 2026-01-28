# Hướng Dẫn Chạy Tests

## Cấu trúc Tests

```
tests/
├── __init__.py
├── test_presentation_reader.py    # Test PresentationReader service
├── test_api_routes.py              # Test API routes
├── test_integration.py              # Integration tests
└── test_file_validation.py          # Test file validation
```

## Cách Chạy Tests

### 1. Chạy tất cả tests:
```bash
python run_tests.py
```

### 2. Chạy từng test file:
```bash
# Test PresentationReader
python -m unittest tests.test_presentation_reader

# Test API routes
python -m unittest tests.test_api_routes

# Test integration
python -m unittest tests.test_integration

# Test file validation
python -m unittest tests.test_file_validation
```

### 3. Chạy với pytest (nếu có cài):
```bash
pip install pytest
pytest tests/
```

### 4. Chạy với coverage:
```bash
pip install coverage
coverage run -m unittest discover tests
coverage report
coverage html  # Tạo HTML report
```

## Test Cases

### test_presentation_reader.py
- ✅ Test đọc file không tồn tại
- ✅ Test file type không hỗ trợ
- ✅ Test structure của kết quả

### test_api_routes.py
- ✅ Test upload không có file
- ✅ Test upload filename rỗng
- ✅ Test upload file type không hợp lệ
- ✅ Test get presentation không tồn tại
- ✅ Test get slides không tồn tại
- ✅ Test get slide cụ thể

### test_integration.py
- ✅ Test full workflow từ upload đến get slides
- ✅ Test với mock data

### test_file_validation.py
- ✅ Test validation file extension
- ✅ Test validation file size
- ✅ Test secure filename

## Lưu Ý

1. **Mock Data**: Một số tests sử dụng mock data vì không có file PPT/PDF thật
2. **File Dependencies**: Để test đầy đủ, cần có file PPT/PDF thật
3. **Temporary Files**: Tests tự động tạo và xóa temporary files

## Thêm Test Mới

Để thêm test mới:

1. Tạo test function trong file test tương ứng
2. Function name phải bắt đầu với `test_`
3. Sử dụng `self.assert*` để kiểm tra kết quả

Ví dụ:
```python
def test_my_new_feature(self):
    """Test mô tả feature mới"""
    # Arrange
    # Act
    # Assert
    self.assertEqual(expected, actual)
```

## CI/CD Integration

Có thể tích hợp vào CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: python run_tests.py
```

