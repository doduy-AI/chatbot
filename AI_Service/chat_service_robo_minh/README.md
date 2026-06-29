# 🤖 Chat Service RoboMinh — AI Worker cho RoboMinh Persona

## 📌 Tổng quan

`chat_service_robo_minh` là AI worker dành cho persona **RoboMinh**. Worker lắng nghe queue `ai_tasks_robo_minh` trên Redis, xử lý câu hỏi bằng **Google VertexAI** kết hợp với **LangChain** chat history. Phiên bản này có cấu trúc tương tự `chat_service` nhưng **RAG đã bị tạm tắt** (code bị comment out).

## 🔄 Luồng hoạt động

```
Redis Queue "ai_tasks_robo_minh"
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
       ├─► Lấy system_prompt từ Redis cache: group:{groupId}:content
       │
       ├─► LangChain chain (KHÔNG có context/RAG):
       │     system_prompt + history (6 msg gần nhất) + input
       │     (context/RAG code đã bị comment out)
       │
       └─► VertexAI (ChatVertexAI) generates response
              │
              ▼
       Publish "tts_tasks" hoặc "chat-respone" → Redis
```

## 📂 Cấu trúc thư mục

```
chat_service_robo_minh/
├── worker.py           # Main loop: BRPOP "ai_tasks_robo_minh" → ThreadPoolExecutor (max 10)
├── ai_engine.py        # AIEngine: VertexAI + LangChain (RAG disabled)
└── redis_manager.py    # Redis client: listen_tasks(), publish(), publishChat()
```

## 🧠 AIEngine

### Model
- **LLM**: `ChatVertexAI` (Google VertexAI) — model cấu hình qua `MODEL_NAME`
- **Embedding Client**: Google GenAI (`genai.Client`) — đã khởi tạo nhưng không dùng (RAG bị tắt)

### Khác biệt với chat_service
| Tính năng | chat_service | chat_service_robo_minh |
|-----------|:-----------:|:----------------------:|
| RAG (Qdrant context) | ✅ Bật | ❌ Tắt (code comment) |
| Qdrant collection | `BHXH` | `BHXH` |
| Chat history limit | 6 messages | 6 messages |
| LLM | ChatVertexAI | ChatVertexAI |
| Embedding | Google GenAI | Google GenAI (không dùng) |

### Key Methods
| Method | Chức năng |
|--------|-----------|
| `generate_response(text, prompt, userId, groupId)` | Sinh câu trả lời (không RAG) |
| `_get_history(sessionId)` | Lấy/khởi tạo chat history |
| `clear_session(userId)` | Xóa lịch sử chat của user |
| `show_history(userId)` | In ra lịch sử chat (debug) |

## 🚀 Cách chạy

```bash
cd AI_Service
python -m chat_service_robo_minh.worker
```

## 📦 Dependencies
- `langchain-google-vertexai` — VertexAI Chat model
- `langchain-core` — LangChain framework
- `google-cloud-aiplatform` — Google Cloud AI Platform
- `google-genai` — Google GenAI SDK
- `qdrant-client` — Qdrant client (import nhưng chưa dùng)
- `redis` — Redis client

## ⚙️ Biến môi trường liên quan
| Biến | Mô tả |
|------|-------|
| `MODEL_NAME` | Tên model VertexAI |
| `MODEL_QDRANT` | Tên model embedding (chưa dùng) |
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `GCP_LOCATION` | Google Cloud region |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path đến GCP service account JSON |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant connection |
| `REDIS_HOST` / `REDIS_PORT` / `PASS_REDIS` | Redis connection |

## ⚠️ Ghi chú

- RAG code (`get_context`) đã bị comment out toàn bộ. Nếu muốn bật lại, uncomment trong `ai_engine.py`.
- Worker vẫn import `qdrant_client` và khởi tạo Qdrant client trong `__init__`.
- Queue sử dụng là `ai_tasks_robo_minh` — khác với `ai_tasks` (human) và `ai_tasks_robot` (Chiko).
