# 📄 Embedding Service — Document Processing & Vector Storage

## 📌 Tổng quan

`embetdding_service` là pipeline xử lý tài liệu và lưu trữ vector. Service lắng nghe queue `embedding_tasks` trên Redis, thực hiện toàn bộ pipeline: **phân loại file → trích xuất văn bản (OCR) → chunking → embedding → upsert vào Qdrant**.

## 🔄 Luồng hoạt động

```
Redis Queue "embedding_tasks"
       │
       ▼
  worker.py (main loop)
       │ BRPOP
       ▼
  worker_process_task(folder_path, folder_path_clean, userId, groupId, base)
       │
       ├─► BƯỚC 1: CLEAR DATA
       │     ├─► Duyệt từng file trong uploads/{userId}/
       │     ├─► classifier.py: Phân loại file
       │     │     ├─ .doc/.docx → "word"
       │     │     ├─ .pdf (có text) → "pdf_word"
       │     │     ├─ .pdf (scan/ảnh) → "pdf_scan"
       │     │     ├─ .txt/.md → "text_ready"
       │     │     └─ .jpg/.png... → "pdf_scan"
       │     │
       │     └─► Trích xuất text:
       │           ├─ word_to_markdown(): python-docx → Markdown
       │           ├─ pdf_word_to_markdown(): pymupdf → Markdown
       │           ├─ pdf_scan_to_markdown(): pymupdf4llm/OCR → Markdown
       │           └─ text_ready: copy trực tiếp
       │     Kết quả: file .md được lưu vào clean/{userId}/
       │
       ├─► BƯỚC 2: CHUNKING
       │     └─► chunk_text(folder_path_clean, userId, groupId, base)
       │           ├─ Đọc từng file .md trong clean/{userId}/
       │           ├─ Split thành chunk 600 words, overlap 50 words
       │           └─► Gọi embedding_engine.process_embedding_for_user()
       │
       └─► BƯỚC 3: EMBEDDING & UPSERT
             └─► process_embedding_for_user(userId, groupId, base, chunk, filename)
                   ├─► SentenceTransformer.encode(chunk) → 384-dim vector
                   ├─► Tạo PointStruct(id=UUID, vector, payload)
                   └─► Qdrant.upsert(collection="bytehome1")
       │
       ▼
  Cleanup: Move files → processed/{clear|uploads}/{userId}/
```

## 📂 Cấu trúc thư mục

```
embetdding_service/
├── worker.py                 # Main loop: BRPOP "embedding_tasks" → process
├── redis_manager.py          # Redis client: listen_tasks(), publish()
├── requirements.txt          # sentence-transformers, qdrant-client, pymupdf...
├── clear_data/               # Document processing
│   ├── router.py             # Orchestrator: duyệt folder → extract → save .md
│   ├── classifier.py         # File type detection
│   ├── extract_word.py       # Word (.doc/.docx) → Markdown
│   └── extract_pdf.py        # PDF → Markdown (text + scan/OCR)
├── chucking/
│   └── chucking.py           # Text splitting: 600-word chunks, 50-word overlap
└── embetding/
    └── embedding_engine.py   # SentenceTransformer + Qdrant client + upsert
```

## 🔧 Các bước xử lý chi tiết

### Bước 1: Phân loại file (`classifier.py`)

```python
classify_file(file_path)
  ├─ .doc / .docx                    → "word"
  ├─ .pdf (text > 100 chars)         → "pdf_word"      # pymupdf extract
  ├─ .pdf (text ≤ 100 chars)         → "pdf_scan"      # OCR
  ├─ .jpg / .png / .bmp / .webp ...  → "pdf_scan"      # OCR
  ├─ .txt / .md                      → "text_ready"     # Copy trực tiếp
  └─ others                          → "unsupported"    # Bỏ qua
```

### Bước 2: Trích xuất văn bản

| File type | Extractor | Công cụ |
|-----------|-----------|---------|
| `word` | `word_to_markdown()` | python-docx |
| `pdf_word` | `pdf_word_to_markdown()` | pymupdf (fitz) |
| `pdf_scan` | `pdf_scan_to_markdown()` | pymupdf4llm / OCR |
| `text_ready` | Copy trực tiếp | shutil.copy2 |

### Bước 3: Chunking (`chucking.py`)

```python
chunk_size = 600 words
overlap    = 50 words

Text: "word1 word2 ... word1000"
  → Chunk 1: words[0:600]
  → Chunk 2: words[550:1000]  # overlap 50
```

### Bước 4: Embedding & Upsert (`embedding_engine.py`)

```python
Collection: "bytehome1"
Vector size: 384
Distance: COSINE

Payload:
  - groupId:  UUID của group
  - userId:   "base" (dữ liệu chung) hoặc userId (dữ liệu riêng)
  - filename: tên file gốc
  - text:     nội dung chunk

Indexes:
  - userId  (KEYWORD)
  - groupId (KEYWORD)
```

## 🗂️ Thư mục làm việc

```
{project_root}/
├── uploads/{userId}/     # File upload của user
├── clean/{userId}/       # File .md sau khi trích xuất
└── processed/
    ├── uploads/{userId}/ # File gốc sau xử lý (đã move)
    └── clear/{userId}/   # File .md sau xử lý (đã move)
```

## 🚀 Cách chạy

```bash
cd AI_Service
python -m embetdding_service.worker
```

Hoặc dùng entry point:
```bash
embetdding
```

## 📦 Dependencies
- `sentence-transformers` — Model embedding (384-dim)
- `qdrant-client` — Vector database client
- `pymupdf` (fitz) — PDF text extraction
- `pymupdf4llm` — PDF OCR / LLM-friendly extraction
- `python-docx` — Word document extraction
- `redis` — Message queue

## ⚙️ Biến môi trường liên quan
| Biến | Mô tả |
|------|-------|
| `MODEL_QDRANT` | Tên SentenceTransformer model (vd: `all-MiniLM-L6-v2`) |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant connection |
| `REDIS_HOST` / `REDIS_PORT` / `PASS_REDIS` | Redis connection |
