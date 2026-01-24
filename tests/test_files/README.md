# Test Files Directory

Đặt các file test PPT/PDF vào thư mục này để chạy tests với file thật.

## Cấu trúc:

```
tests/test_files/
├── test.pptx    # File PowerPoint test (optional)
├── test.pdf     # File PDF test (optional)
└── README.md     # File này
```

## Lưu ý:

- Các file test này sẽ được sử dụng bởi `test_with_real_files.py`
- Nếu không có file, tests sẽ tự động skip
- Không commit file lớn vào git (thêm vào .gitignore)

## Tạo file test đơn giản:

### PowerPoint:
- Tạo file PPTX với 2-3 slides
- Mỗi slide có một ít text để test

### PDF:
- Tạo file PDF với 2-3 pages
- Mỗi page có một ít text để test

