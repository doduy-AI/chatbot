#  TTS Service


---

##  Yêu cầu hệ thống

* Python **3.10**
* pip (Python package manager)

---

## ⚙️ Cài đặt

### 1. Tạo môi trường ảo (khuyến nghị)

```bash
conda 
conda create -n abc python=3.10 -y 
conda activate abc
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Chạy test

Sau khi cài đặt xong, chạy file kiểm tra:

```bash
python3 check.py
```

Nếu mọi thứ hoạt động bình thường, hệ thống sẽ:

* Load model TTS
* Generate audio từ text mẫu
* Xuất file hoặc stream audio (tuỳ config)

---

## 📁 Cấu trúc cơ bản

```
.
├── requirements.txt   # Danh sách thư viện
├── check.py           # Script test TTS
├── models/            # Model TTS 
├── output/            # File audio output
└── ...
```

---

## 🧪 Mục đích

* Test nhanh pipeline TTS
* Kiểm tra chất lượng audio
* Debug các lỗi liên quan đến model hoặc streaming

---

## ⚠️ Lưu ý

* Đảm bảo Python đúng version **3.10**
* Nếu gặp lỗi thiếu thư viện → thử:

```bash
pip install --upgrade pip setuptools
```

* Với các model lớn, cần đảm bảo đủ RAM/GPU (nếu có)

---

