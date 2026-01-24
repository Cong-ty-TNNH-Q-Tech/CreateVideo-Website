# 🚀 Quick Start - Chạy Tests

## ⚡ Cách Nhanh Nhất:

### 1. Cài đặt dependencies:
```bash
pip install python-pptx pypdf
```

### 2. Chạy tests:
```bash
python run_tests.py
```

## 📝 Chi Tiết:

### Nếu chưa cài dependencies:
Tests sẽ tự động **skip** các test cần dependencies và chỉ chạy các test không cần dependencies (như file validation).

### Nếu đã cài dependencies:
Tất cả tests sẽ chạy bình thường.

## ✅ Kết Quả:

- **OK**: Tất cả tests pass
- **SKIP**: Test bị skip (thiếu dependencies hoặc file test)
- **FAIL**: Test fail (cần fix)

## 🔧 Troubleshooting:

### Lỗi: "ModuleNotFoundError: No module named 'pptx'"
```bash
pip install python-pptx pypdf
```

### Lỗi: "Cannot import app"
Đảm bảo đang chạy từ thư mục gốc của project:
```bash
cd d:\CreateVideo-Website
python run_tests.py
```

