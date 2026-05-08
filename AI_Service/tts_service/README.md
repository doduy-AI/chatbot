# 🚀 Chatbot Voice - Setup Guide

## 📌 Bước 1: Chạy Colab
- Mở link:
  https://colab.research.google.com/drive/1t6GaB5oDh2SrBBDhx6QMHW_BkXRzAD6k?usp=sharing
- Chạy **2 ô bên trái**
- Sau khi chạy xong, copy **URL public** được trả ra

---

## 📌 Bước 2: Clone project
```bash
git clone https://github.com/bytehomerepo/chatbot_voice
cd chatbot_voice
git checkout doduy_tts

```

## 📌 Bước 2: Clone project
```bash
cd AI_Service/tts_service
uv sync
```

## 📌 Bước 3: Cấu hình ENV
``` bash

sudo apt install nano
nano .env
Dán file .env (sẽ được cung cấp riêng)
Sửa giá trị:
EXTERNAL_HOST=localhost:8001
thành 
EXTERNAL_HOST=<URL từ Colab bước 1>

```


## 📌 Bước 5: Chạy service
```bash
uv run wordker.py

```