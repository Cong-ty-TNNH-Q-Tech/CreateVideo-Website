# 🧪 Quick Test Guide

## ✅ Server Đã Khởi Động!

### 🌐 Truy Cập Ngay:

**URL**: http://localhost:5000

---

## 📋 Test Flow Chi Tiết:

### ✅ Bước 1: Upload Presentation

1. **Mở browser**: http://localhost:5000
2. **Upload file**:
   - Click vào vùng upload (có icon file)
   - Hoặc drag & drop file PPT/PDF vào
   - Chọn file từ dialog
3. **Click "Upload và Đọc File"**
4. **Kiểm tra**:
   - ✅ File được upload
   - ✅ Slides preview hiển thị
   - ✅ Nội dung từng slide được đọc

### ✅ Bước 2: Generate Text (Cần Gemini API Key)

**⚠️ Lưu ý**: Cần có Gemini API key trong file `.env`

1. **Click "Tiếp tục → Bước 2: Generate Text"**
2. **Xem danh sách slides** với textarea
3. **Click "Generate Text"** cho slide đầu tiên
4. **Kiểm tra**:
   - ✅ Text được generate (nếu có API key)
   - ✅ Hoặc hiển thị error message (nếu chưa có API key)
5. **Edit text** nếu cần
6. **Click "Save"** để lưu

---

## 🔧 Nếu Có Vấn Đề:

### Server không chạy:
```bash
# Kiểm tra port
netstat -ano | findstr :5000

# Chạy lại
python app.py
```

### Bước 2 không hoạt động:
1. **Kiểm tra file `.env`**:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```
2. **Lấy API key**: https://makersuite.google.com/app/apikey
3. **Restart server** sau khi thêm API key

### Lỗi import:
```bash
# Cài lại dependencies
pip install python-pptx pypdf google-generativeai python-dotenv
```

---

## 📊 Test Checklist:

### Bước 1:
- [ ] Server chạy (http://localhost:5000)
- [ ] Frontend hiển thị
- [ ] Upload file thành công
- [ ] Preview slides hiển thị
- [ ] Nội dung slides được đọc đúng

### Bước 2:
- [ ] Step 2 section hiển thị
- [ ] Generate Text button hoạt động
- [ ] Text được generate (nếu có API key)
- [ ] Edit text hoạt động
- [ ] Save button hoạt động

---

## 🎯 Expected Results:

### Bước 1 (Không cần API key):
- ✅ Upload file PPT/PDF
- ✅ Đọc nội dung slides
- ✅ Hiển thị preview

### Bước 2 (Cần API key):
- ✅ Generate text từ Gemini
- ✅ Edit và save text
- ✅ Text được lưu vào JSON

---

**Server đang chạy! Mở browser và test ngay! 🚀**

