# 🤖 Chat Service — AI Worker cho người dùng Web

## 📌 Tổng quan

`chat_service` là AI worker phục vụ người dùng **web** (human). Worker lắng nghe queue `ai_tasks` trên Redis, xử lý câu hỏi bằng **Google VertexAI** kết hợp với **RAG (Retrieval-Augmented Generation)** từ Qdrant, và trả về kết quả qua Redis PubSub.

## 🔄 Luồng hoạt động

```
Redis Queue "ai_tasks"
       │
       ▼
  worker.py (main loop)
       │ BRPOP
       ▼
  handle_task(data)
       │
       ▼
  AIEngine.generate_response(text, prompt, userId, groupId)
       │
       ├─► get_context(userId, groupId, text)
       │     ├─► Embed query bằng Google GenAI embedding model
       │     ├─► Query Qdrant collection "BHXH" with filters:
       │     │     - groupId = group_id
       │     │     - userId IN (base, user_id)
       │     └─► Trả về top 10 chunk liên quan nhất
       │
       ├─► LangChain chain:
       │     system_prompt + history (6 msg gần nhất) + context + input
       │
       └─► VertexAI (ChatVertexAI) generates response
              │
              ▼
       Publish "tts_tasks" hoặc "chat-respone" → Redis
```

## 📂 Cấu trúc thư mục

```
chat_service/
├── worker.py           # Main loop: BRPOP "ai_tasks" → ThreadPoolExecutor
├── ai_engine.py        # AIEngine class: VertexAI + LangChain + Qdrant RAG
├── redis_manager.py    # Redis client: listen_tasks(), publish(), publishChat()
└── Evals/
    └── LLMQA.py        # LLM evaluation scripts
```

## 🧠 AIEngine

### Model
- **LLM**: `ChatVertexAI` (Google VertexAI) — model được cấu hình qua biến môi trường `MODEL_NAME`
- **Embedding**: Google GenAI embedding model (qua `MODEL_QDRANT`)

### RAG Pipeline (`get_context`)
1. Nhận `query_text` từ người dùng
2. Embed query bằng Google GenAI embedding
3. Query Qdrant collection `BHXH` với filter:
   - `groupId` = group hiện tại
   - `userId` = `"base"` (dữ liệu chung) hoặc `userId` hiện tại (dữ liệu riêng)
4. Deduplicate theo nội dung
5. Trả về danh sách context (title, section_path, file_name, content)

### Chat History
- Dùng `InMemoryChatMessageHistory` của LangChain
- Giới hạn **6 tin nhắn gần nhất** để tiết kiệm token
- Hỗ trợ `clear_session(userId)` để reset lịch sử

### Key Methods
| Method | Chức năng |
|--------|-----------|
| `generate_response(text, prompt, userId, groupId)` | Sinh câu trả lời từ input |
| `get_context(userId, groupId, queryText)` | Truy vấn Qdrant lấy context |
| `_get_history(sessionId)` | Lấy/khởi tạo chat history |
| `clear_session(userId)` | Xóa lịch sử chat của user |
| `show_history(userId)` | In ra lịch sử chat (debug) |

## 🚀 Cách chạy

```bash
cd AI_Service
python -m chat_service.worker
```

Hoặc dùng entry point đã đăng ký:
```bash
chat
```

## 📦 Dependencies
- `langchain-google-vertexai` — VertexAI Chat model
- `langchain-core` — LangChain framework
- `google-cloud-aiplatform` — Google Cloud AI Platform
- `google-genai` — Google GenAI SDK (embedding)
- `qdrant-client` — Qdrant vector search
- `redis` — Redis client

## ⚙️ Biến môi trường liên quan
| Biến | Mô tả |
|------|-------|
| `MODEL_NAME` | Tên model VertexAI |
| `MODEL_QDRANT` | Tên model embedding |
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `GCP_LOCATION` | Google Cloud region |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path đến GCP service account JSON |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant connection |
| `REDIS_HOST` / `REDIS_PORT` / `PASS_REDIS` | Redis connection |
