# 🧒 Chat Service Robot — AI Worker cho Robot Chiko

## 📌 Tổng quan

`chat_service_robot` là AI worker dành cho **robot vật lý** — sử dụng persona **Chiko** (robot đến từ hành tinh kẹo dẻo). Worker lắng nghe queue `ai_tasks_robot` trên Redis, xử lý giọng nói của trẻ em bằng **Google Gemini (GenAI)**, tích hợp **conversation summarization** thông minh, và hỗ trợ đa chế độ: tiếng Việt, English mode, correction mode.

## 🔄 Luồng hoạt động

```
Redis Queue "ai_tasks_robot"
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
       ├─► Lấy summary (structured memory) từ self.summary_memories[userId]
       │
       ├─► LangChain chain:
       │     system_prompt + summary (internal_context) + history + input
       │
       ├─► Gemini generates response
       │
       ├─► clean_response(): Kiểm tra banned words (tóm tắt, memory, bộ nhớ...)
       │
       ├─► Nếu history > 6 msg → background thread _summarize()
       │     └─► Tạo JSON summary: language_mode, correction_mode,
       │          current_activity, child_profile, important_facts...
       │
       └─► clean_llm_text(): Xóa markdown, emoji, ký tự đặc biệt cho TTS
              │
              ▼
       Publish "tts_tasks" → Redis
```

## 📂 Cấu trúc thư mục

```
chat_service_robot/
├── worker.py           # Main loop: BRPOP "ai_tasks_robot" → ThreadPoolExecutor (max 10)
├── ai_engine.py        # AIEngine: Gemini GenAI + LangChain + Summarization
├── redis_manager.py    # Redis client: listen_tasks(), publish(), publishChat(), get_cache()
├── Dockerfile          # Docker image
├── docker-compose.yml  # Scale: --scale ai_worker=5
├── requirements.txt    # google-genai, redis, python-dotenv, pydantic-settings...
├── utils/
│   └── cleanText.py    # LLM response cleaner (strip markdown, emoji, newlines)
└── Evals/
    └── LLMQA.py        # LLM evaluation
```

## 🧠 AIEngine — Chiko Persona

### Model
- **LLM**: `ChatGoogleGenerativeAI` (Google Gemini) — model cấu hình qua `MODEL_NAME`
- **Summary Model**: Cùng model Gemini, nhưng output JSON với `response_mime_type="application/json"`

### Tính năng đặc biệt

#### 1. Multi-Language Mode
- **Mặc định**: tiếng Việt
- **English mode**: Tự động bật khi bé nói câu tiếng Anh có chủ ngữ + động từ
- Không bật nếu chỉ nói 1 từ tiếng Anh lẻ
- Trong English mode: CHỈ dùng tiếng Anh, giải thích từ mới bằng tiếng Việt ngắn sau dấu gạch ngang

#### 2. Correction Mode
- Bật khi bé nói muốn được sửa hoặc luyện tập tiếng Anh
- Luôn khích lệ trước khi sửa lỗi
- Không dùng thuật ngữ ngữ pháp phức tạp
- Không tự ý bịa thêm nội dung

#### 3. Conversation Summarization
Sau mỗi 6 tin nhắn, background thread tạo structured JSON summary lưu vào `self.summary_memories`:

```json
{
  "language_mode": "vi | en",
  "correction_mode": true/false,
  "current_activity": "free_talk | english_practice | correction_practice | story | quiz | unknown",
  "child_profile": {
    "name": null,
    "age": null,
    "interests": []
  },
  "recent_topic": "",
  "important_facts": [],
  "last_user_intent": "",
  "do_not_reveal": true
}
```

**Quy tắc an toàn**:
- KHÔNG lưu địa chỉ, số điện thoại, trường học, thông tin nhạy cảm
- `do_not_reveal` luôn `true` → system prompt cấm AI nói về internal context

#### 4. Child Safety
- Không bạo lực, không nội dung không phù hợp
- Chuyện ma được phép nhưng phải vui, không đáng sợ
- Nếu bé hỏi nội dung không phù hợp → chuyển hướng nhẹ nhàng

#### 5. TTS-Friendly Output
- Không markdown, không emoji, không bullet point
- Không ngoặc đơn, ngoặc kép, ký tự trang trí
- Viết số thành chữ (ba thay vì 3)
- Ngắt câu tự nhiên để TTS đọc mượt

### Key Methods
| Method | Chức năng |
|--------|-----------|
| `generate_response(text, prompt, userId, groupId)` | Sinh câu trả lời từ input, kèm summary context |
| `_summarize(sessionId, messages)` | Tạo structured JSON summary từ đoạn hội thoại cũ |
| `_normalize_summary(data)` | Validate & normalize summary JSON |
| `_default_summary()` | Trả về default summary structure |
| `clean_response(text)` | Kiểm tra banned words (tóm tắt, memory, bộ nhớ...) |
| `clear_session(userId)` | Xóa cả history + summary của user |

## 🚀 Cách chạy

### Chạy trực tiếp
```bash
cd AI_Service
python -m chat_service_robot.worker
```

### Chạy với Docker Compose (có thể scale)
```bash
cd AI_Service/chat_service_robot
docker compose up --scale ai_worker=5
```

### Entry point
```bash
chat_robot
```

## 📦 Dependencies
- `google-genai` — Google Gemini GenAI SDK
- `langchain-google-genai` — LangChain + Gemini integration
- `langchain-core` — LangChain framework (prompts, history, runnables)
- `redis` — Redis client
- `python-dotenv` / `pydantic-settings` — Environment config

## ⚙️ Biến môi trường liên quan
| Biến | Mô tả |
|------|-------|
| `MODEL_NAME` | Tên model Gemini (vd: `gemini-2.5-flash`) |
| `SUMMARY_MODEL_NAME` | Tên model cho summarization |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `REDIS_HOST` / `REDIS_PORT` / `PASS_REDIS` | Redis connection |
