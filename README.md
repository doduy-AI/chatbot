# 📚 Tài liệu dự án Chatbot Voice AI

## 📌 Tổng quan

**Chatbot Voice AI** là hệ thống chatbot giọng nói thời gian thực dành cho trẻ em, được xây dựng theo kiến trúc **microservice**. Hệ thống cho phép giao tiếp hai chiều qua giọng nói: nhận diện giọng nói (STT) → xử lý ngôn ngữ (LLM) → tổng hợp giọng nói (TTS) → phát lại cho người dùng. Hỗ trợ cả người dùng thông thường (giao diện web) và robot vật lý (truyền audio stream qua WebSocket).

### Công nghệ lõi

| Lĩnh vực | Công nghệ |
|----------|-----------|
| Backend API | Node.js + Express 5 |
| AI Engine | Python + LangChain + Google Gemini (GenAI) |
| Realtime Communication | WebSocket (ws) |
| Message Queue / Cache | Redis |
| Database | PostgreSQL + Sequelize ORM |
| Vector Database | Qdrant (384-dim embeddings) |
| STT (Speech-to-Text) | Soniox (stt-rt-v4, 48kHz, PCM 16-bit) |
| TTS (Text-to-Speech) | Bytehome_TTS |
| Embedding Model | Sentence Transformers (384-dim) |
| Frontend Web | React 19 + Vite + TailwindCSS v4 |
| Containerization | Docker + Docker Compose |
| Client Robot | Python (PyAudio, WebSocket) |

---

## 🏗️ Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                             │
│                                                                   │
│  ┌──────────────────┐     ┌──────────────────────────────────┐   │
│  │   Web Browser     │     │   Robot Client (Python)          │   │
│  │   (React SPA)     │     │   - Microphone capture (48kHz)   │   │
│  │   port 4001       │     │   - WebSocket audio streaming   │   │
│  │                   │     │   - Audio playback (streaming)   │   │
│  └────────┬──────────┘     └───────────────┬──────────────────┘   │
│           │ HTTP REST                       │ WebSocket + Binary   │
└───────────┼─────────────────────────────────┼──────────────────────┘
            │                                 │
            ▼                                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                        BACKEND (Node.js :3000)                     │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Auth Service    │  │  REST API Router │  │  WebSocket       │  │
│  │  - Register      │  │  - /auth/*       │  │  Server          │  │
│  │  - Login (JWT)   │  │  - /api/*        │  │  - chat.socket   │  │
│  │  - Middleware     │  │  - /api/admin/*  │  │  - Soniox STT    │  │
│  └─────────────────┘  │  - /rag/*         │  │  - Redis pub/sub │  │
│                        └──────────────────┘  └─────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  RedisService (ioredis)                                      │ │
│  │  - Publisher: push tasks to AI queues                        │ │
│  │  - Subscriber: listen voice_ready:* pattern                  │ │
│  │  - Cache: group prompts & summaries (TTL 3600s)              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬──────────────────────────────────────┘
                             │ Redis (port 9736)
                             │
        ┌────────────────────┼────────────────────────────┐
        ▼                    ▼                            ▼
┌───────────────┐  ┌──────────────────┐  ┌─────────────────────────┐
│ ai_tasks      │  │ ai_tasks_robot   │  │ ai_tasks_robo_minh      │
│ (Human chat)  │  │ (Robot chat)     │  │ (RoboMinh chat)         │
└───────┬───────┘  └────────┬─────────┘  └────────────┬────────────┘
        │                   │                         │
        ▼                   ▼                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (Python)                            │
│                                                                   │
│  ┌────────────────────┐  ┌───────────────────────────────────┐  │
│  │ chat_service/      │  │ chat_service_robot/               │  │
│  │ worker.py          │  │ worker.py                         │  │
│  │ Queue: ai_tasks    │  │ Queue: ai_tasks_robot             │  │
│  │ ┌───────────────┐  │  │ ┌──────────────────────────────┐  │  │
│  │ │ AIEngine       │  │  │ │ AIEngine (Chiko persona)     │  │  │
│  │ │ - Gemini LLM   │  │  │ │ - Gemini LLM                 │  │  │
│  │ │ - LangChain     │  │  │ │ - LangChain                  │  │  │
│  │ │ - Chat History  │  │  │ │ - Chat History + Summary     │  │  │
│  │ │                 │  │  │ │ - Conversation summarization │  │  │
│  │ └───────────────┘  │  │ │ - Child-friendly persona      │  │  │
│  └────────────────────┘  │ └──────────────────────────────┘  │  │
│                          └───────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ chat_service_robo_minh/  (Separate AI instance)           │    │
│  │ worker.py | Queue: ai_tasks_robo_minh                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────┐  ┌───────────────────────────────────┐  │
│  │ TTS Service         │  │ Embedding Service                 │  │
│  │ (FastAPI :5000)     │  │ worker.py                        │  │
│  │ ┌─────────────────┐ │  │ Queue: embedding_tasks           │  │
│  │ │ Bytehome_TTS Model  │ │  │ ┌──────────────────────────────┐│  │
│  │ │ - Voice cloning  │ │  │ │ Document Processing Pipeline ││  │
│  │ │ - Streaming TTS  │ │  │ │ 1. File Classification       ││  │
│  │ │ - MP3 / PCM WAV  │ │  │ │ 2. OCR / Text Extraction     ││  │
│  │ │ - Multi-voice    │ │  │ │ 3. PDF, Word → Markdown      ││  │
│  │ │   (nutrem,       │ │  │ │ 4. Text Chunking             ││  │
│  │ │    nuhanoi, nam) │ │  │ │ 5. Sentence Embedding        ││  │
│  │ └─────────────────┘ │  │ │ 6. Qdrant Upsert             ││  │
│  │ /stream-voice/{id}  │  │ └──────────────────────────────┘│  │
│  └────────────────────┘  └───────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐
│   PostgreSQL :5431   │  │   Qdrant :6333      │
│   - Users            │  │   Collection:        │
│   - Groups           │  │     bytehome1        │
│   - Roles            │  │   - userId index     │
│   - Prompts          │  │   - groupId index    │
│   - SummaryPrompts   │  │   - 384-dim vectors  │
└─────────────────────┘  └─────────────────────┘
```

---

## 📂 Cấu trúc thư mục chi tiết

```
chatbot_voice/
├── src/                                    # Backend Node.js
│   ├── app.js                              # Entry point: Express + WebSocket + DB
│   ├── config/
│   │   ├── db.js                           # Sequelize PostgreSQL connection
│   │   ├── server.js                       # Environment config loader
│   │   └── multer.config.js                # File upload config
│   ├── model/
│   │   ├── index.js                        # Model associations & relationships
│   │   ├── user.model.js                   # User (id, username, password, role, group)
│   │   ├── group.model.js                  # Group (groupId, groupName, email, phone)
│   │   ├── role.model.js                   # Role (roleid)
│   │   ├── group_prompt.model.js           # System prompt per group
│   │   └── summary_prompt.model.js         # Summary prompt per group
│   ├── controllers/
│   │   ├── auth.controller.js              # Register, Login (bcrypt + JWT)
│   │   ├── group.controller.js             # Group CRUD
│   │   ├── rag.controller.js               # RAG upload & query
│   │   ├── Admin/                          # Admin panel controllers
│   │   │   ├── user.controller.js
│   │   │   ├── group.controller.js
│   │   │   ├── rag.controller.js
│   │   │   ├── promt.controller.js
│   │   │   └── summaryPrompt.controller.js
│   │   └── client/
│   │       ├── chat.controller.js          # Client chat endpoint
│   │       └── rag.controller.js
│   ├── middlewares/
│   │   ├── auth.middleware.js              # WebSocket JWT verify
│   │   └── authAPI.middleware.js           # REST API JWT verify + Admin check
│   ├── router/
│   │   ├── index.router.js                 # Main router aggregator
│   │   ├── auth.router.js
│   │   ├── rag.router.js
│   │   ├── Admin/
│   │   │   ├── index.router.js             # Admin routes (requires isAdmin)
│   │   │   ├── user.router.js
│   │   │   ├── group.router.js
│   │   │   ├── rag.router.js
│   │   │   └── prompt.router.js
│   │   └── Client/
│   │       └── index.router.js
│   ├── services/
│   │   ├── redisService.js                 # Redis pub/sub, cache, task queues
│   │   └── sonioxHandler.Service.js        # Soniox STT session handler (Robot)
│   └── sockets/
│       └── chat.socket.js                  # WebSocket controller (human + robot)
│
├── AI_Service/                             # AI Microservices (Python)
│   ├── .env                                # Environment variables
│   ├── requirements.txt                    # Top-level dependencies
│   ├── pyproject.toml                      # Python package config
│   ├── config/
│   │   └── config.py                       # Pydantic Settings (shared config)
│   ├── chat_service/                       # AI worker for human users
│   │   ├── worker.py                       # Listens on ai_tasks queue
│   │   ├── ai_engine.py                    # LangChain + Gemini LLM engine
│   │   ├── redis_manager.py                # Redis connection & operations
│   │   └── Evals/
│   │       └── LLMQA.py                    # LLM evaluation
│   ├── chat_service_robot/                 # AI worker for robot (Chiko persona)
│   │   ├── worker.py                       # Listens on ai_tasks_robot queue
│   │   ├── ai_engine.py                    # Child-friendly Chiko AI engine
│   │   ├── redis_manager.py
│   │   ├── Dockerfile                      # Docker image for robot worker
│   │   ├── docker-compose.yml              # Scale: --scale ai_worker=5
│   │   ├── requirements.txt
│   │   ├── utils/
│   │   │   └── cleanText.py                # LLM response cleaner
│   │   └── Evals/
│   │       └── LLMQA.py
│   ├── chat_service_robo_minh/             # AI worker for RoboMinh persona
│   │   ├── worker.py                       # Listens on ai_tasks_robo_minh queue
│   │   ├── ai_engine.py
│   │   └── redis_manager.py
│   ├── tts_service/                        # Text-to-Speech service
│   │   ├── wordker.py                      # FastAPI app + streaming TTS endpoint
│   │   ├── tts_service.py                  # OmniVoice TTS engine wrapper
│   │   ├── dowload_model.py                # HuggingFace model downloader
│   │   ├── config/
│   │   │   ├── config.py                   # TTS-specific config
│   │   │   └── redis_maneger.py
│   │   ├── input/
│   │   │   └── voice_profiles.py           # Voice definitions (nutrem, nuhanoi, nam)
│   │   ├── omnivoice/                      # OmniVoice TTS library
│   │   │   ├── cli/                        # CLI tools (train, infer, demo)
│   │   │   ├── data/                       # Data processing (batching, dataset)
│   │   │   ├── eval/                       # Evaluation (MOS, WER, similarity)
│   │   │   ├── models/                     # Model architecture
│   │   │   ├── scripts/                    # Audio processing utilities
│   │   │   ├── training/                   # Training pipeline
│   │   │   └── utils/                      # Audio, text, voice design utilities
│   │   ├── docker-compose.yaml
│   │   └── dockerfile
│   ├── embetdding_service/                 # Document embedding pipeline
│   │   ├── worker.py                       # Listens on embedding_tasks queue
│   │   ├── redis_manager.py
│   │   ├── requirements.txt
│   │   ├── chucking/
│   │   │   └── chucking.py                 # Text chunking & Qdrant upsert
│   │   ├── clear_data/
│   │   │   ├── router.py                   # Document processing orchestrator
│   │   │   ├── classifier.py               # File type detection
│   │   │   ├── extract_pdf.py              # PDF → Markdown (text & OCR)
│   │   │   └── extract_word.py             # Word → Markdown
│   │   └── embetding/
│   │       └── embedding_engine.py          # Qdrant vector store + Sentence Transformers
│   ├── docker/
│   │   ├── Dockerfile.chat_BHXH
│   │   ├── Dockerfile.chat_chiko
│   │   └── Dockerfile.chat_robo_minh
│   ├── chiko-495710-493fd37069f6.json      # GCP service account (gitignored)
│   └── gen-lang-client-0954243606-4d0f4019a524.json
│
├── client/                                 # Robot client application
│   ├── main.py                             # Entry point: mic → WS → play audio
│   ├── uploadFile.py                       # File upload script
│   ├── pyproject.toml
│   ├── logic/
│   │   ├── data_mic.py                     # PyAudio microphone streamer (48kHz)
│   │   ├── ws_handler.py                   # WebSocket client + audio playback
│   │   ├── login.py                        # REST API login + token retrieval
│   │   ├── sound.py                        # Audio stream player
│   │   └── checkwifi.py                    # Network connectivity check
│   └── .python-version
│
├── ui-ux/                                  # Web frontend (React SPA)
│   ├── index.html
│   ├── vite.config.js                      # Vite config, port 4001
│   ├── package.json
│   ├── public/
│   │   ├── favicon.svg
│   │   ├── favicon.ico.png
│   │   ├── icons.svg
│   │   └── logo.webp
│   └── src/
│       ├── main.jsx                        # React entry
│       ├── App.jsx                         # React Router setup
│       ├── App.css
│       ├── index.css                       # TailwindCSS
│       └── components/
│           ├── RootLayout.jsx
│           ├── Login.jsx                   # Login page
│           └── Home.jsx                    # Chat interface
│
├── docker-compose.yml                      # Infrastructure services (DB, Redis, Qdrant)
├── package.json                            # Node.js backend dependencies
├── Dockerfile                              # Empty placeholder
└── README.md                               # Project overview
```

---

## 🔄 Luồng dữ liệu (Data Flow)

### Luồng 1: Người dùng Web (Human)

```
1. Browser (React) → POST /api/chat → Backend (Express)
2. Backend → redisService.pushTask(task) → Redis queue "ai_tasks"
3. chat_service/worker.py (Python) ← BRPOP "ai_tasks" ← Redis
4. AIEngine.generate_response(text, prompt, userId, groupId)
   ├── LangChain chain: system_prompt + summary + history + input
   ├── Google Gemini generates response
   └── Conversation summarization (background thread, after 6+ messages)
5. Worker → redis_manager.publish("tts_tasks") → Redis queue "tts_tasks"
6. tts_service/wordker.py ← BRPOP "tts_tasks" ← Redis
7. OmniVoice generates streaming audio chunks
8. TTS → redis_manager.publish(f"voice_ready:{userId}") → Redis PubSub
9. Backend (RedisService) → listenForResponses → WebSocket broadcast
10. Browser ← WebSocket ← {type: "AI_VOICE_REPLY", text, audioUrl}
```

### Luồng 2: Robot Client (with STT)

```
1. Robot mic (48kHz PCM 16-bit) → WebSocket binary → Backend
2. Backend → Soniox STT session (real-time transcription)
3. Soniox returns final text (with 1.3s silence detection)
4. Backend → redisService.pushTaskRobot(task) → Redis queue "ai_tasks_robot"
5. chat_service_robot/worker.py ← BRPOP "ai_tasks_robot" ← Redis
6. Chiko AIEngine generates child-friendly response
   ├── Conversation summarization with structured JSON memory
   ├── Language mode: vi/en switching
   ├── Correction mode for English practice
   └── Activity tracking: free_talk, english_practice, story, quiz
7. Worker → redis_manager.publish("tts_tasks") → Redis queue "tts_tasks"
8. TTS Service → voice_ready:{userId} → Redis PubSub
9. Backend → WebSocket → {type: "AI_VOICE_REPLY", text, audioUrl}
10. Robot client → streaming audio player → speaker output
```

### Luồng 3: Document Embedding (RAG)

```
1. User uploads files (PDF, Word, text)
2. Backend → redisService.pushEmbeddingTask(task) → Redis queue "embedding_tasks"
3. embetdding_service/worker.py ← BRPOP "embedding_tasks"
4. Document Pipeline:
   ├── classifier.py: Detect file type (word, pdf_word, pdf_scan, text_ready)
   ├── extract_pdf.py / extract_word.py: Extract text → Markdown
   ├── chucking.py: Split text into chunks
   └── embedding_engine.py: Sentence Transformers → Qdrant upsert (384-dim)
5. Files moved to processed/ directory after completion
```

---

## 🗄️ Cơ sở dữ liệu

### PostgreSQL Schema

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│   Role    │     │  Group    │     │    User       │
├──────────┤     ├──────────┤     ├───────────────┤
│ roleid PK │◄────│ groupId PK│◄────│ id PK (UUID)  │
│           │     │ groupName │     │ roleid FK     │
│           │     │ email     │     │ groupId FK    │
│           │     │ phoneNumber│    │ username      │
│           │     │           │     │ password      │
│           │     │           │     │ clientType    │
│           │     │           │     │  (human|robot)│
└──────────┘     └─────┬─────┘     └───────────────┘
                       │
                       │ 1:1
                       ▼
               ┌──────────────┐     ┌──────────────────┐
               │   prompt      │     │ summary_prompt   │
               ├──────────────┤     ├──────────────────┤
               │ id PK (UUID) │◄────│ promptId FK      │
               │ groupId FK   │     │ summary_prompt   │
               │ promptName   │     └──────────────────┘
               │ content TEXT │
               └──────────────┘
```

### Quan hệ:
- **Role → User**: 1-N (một role có nhiều user)
- **Group → User**: 1-N (một group có nhiều user)
- **Group → Prompt**: 1-1 (một group có một system prompt)
- **Prompt → SummaryPrompt**: 1-1 (một prompt có một summary prompt)

---

## 🔑 Các queue Redis

| Queue/Topic | Loại | Producer | Consumer |
|-------------|------|----------|----------|
| `ai_tasks` | List (LPUSH/BRPOP) | Backend (human) | chat_service/worker.py |
| `ai_tasks_robot` | List (LPUSH/BRPOP) | Backend (robot) | chat_service_robot/worker.py |
| `ai_tasks_robo_minh` | List (LPUSH/BRPOP) | Backend | chat_service_robo_minh/worker.py |
| `tts_tasks` | List (LPUSH/BRPOP) | AI workers | tts_service/wordker.py |
| `embedding_tasks` | List (LPUSH/BRPOP) | Backend | embetdding_service/worker.py |
| `voice_ready:*` | PubSub Pattern | TTS service | Backend (RedisService) |
| `chat-respone` | PubSub Channel | chat_service/worker | Backend (RedisService) |

### Cache Keys:
- `group:{groupId}:content` — System prompt cache (TTL: 3600s)
- `summary:{groupId}:summary` — Summary prompt cache (TTL: 3600s)

---

## 🎭 AI Engine: Chiko Persona (chat_service_robot)

### Tính năng đặc biệt của Chiko:

1. **Multi-language mode**: Tự động chuyển giữa tiếng Việt và English mode dựa trên input của bé
2. **Correction mode**: Luyện tập tiếng Anh, sửa lỗi nhẹ nhàng, luôn khích lệ trước
3. **Conversation summarization**: Sau mỗi 6 tin nhắn, tóm tắt hội thoại thành structured JSON memory
4. **Activity tracking**: free_talk, english_practice, correction_practice, story, quiz
5. **Child safety**: Không bạo lực, không nội dung không phù hợp, không lưu thông tin nhạy cảm
6. **TTS-friendly output**: Không markdown, không emoji, không ký tự đặc biệt

### Structured Memory Format:
```json
{
  "language_mode": "vi | en",
  "correction_mode": true/false,
  "current_activity": "free_talk | english_practice | correction_practice | story | quiz",
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

---

## 🔊 TTS Service

### Voice Profiles:
| Profile | Description | Reference Audio |
|---------|-------------|-----------------|
| `nutrem` | Giọng trẻ em, thân thiện | nutrem.wav |
| `nuhanoi` | Giọng nữ Hà Nội | giongnuhanoi6s.wav |
| `nam` | Giọng nam | nam.wav |

### Streaming Architecture:
- Mỗi câu trả lời được chia thành các chunk nhỏ (≤30 từ, merge nếu <5 từ)
- Từng chunk được generate và stream ngay qua FastAPI StreamingResponse
- Hỗ trợ output: MP3 (lameenc, 128kbps) hoặc raw PCM WAV
- URL endpoint: `/stream-voice/{task_id}?audio_format=mp3`

---

## 🚀 Cách chạy hệ thống

### Infrastructure:
```bash
docker compose up -d       # PostgreSQL, Redis, Qdrant
```

### Backend:
```bash
npm install
npm run dev                # port 3000
```

### AI Workers (có thể scale):
```bash
cd AI_Service
# Chat service (human)
python -m chat_service.worker

# Chat service (robot - Chiko)
python -m chat_service_robot.worker

# Chat service (robo_minh)
python -m chat_service_robo_minh.worker

# TTS service
python -m tts_service.wordker       # port 5000

# Embedding service
python -m embetdding_service.worker
```

Hoặc dùng Docker Compose cho robot workers:
```bash
cd AI_Service/chat_service_robot
docker compose up --scale ai_worker=5
```

### Frontend:
```bash
cd ui-ux
npm run dev                # port 4001
```

### Robot Client:
```bash
cd client
python main.py
```

---

## 🔐 Authentication Flow

1. Client đăng ký/đăng nhập qua `POST /auth/login`
2. Backend trả về JWT token (hết hạn 30 ngày)
3. WebSocket connection: token được gửi qua query parameter `?token=xxx`
4. Middleware `veryConnection` xác thực JWT trước khi upgrade connection
5. REST API routes: `verifyToken` middleware kiểm tra Bearer token
6. Admin routes: thêm `isAdmin` middleware kiểm tra role

---

## 📝 Ghi chú kỹ thuật

- **Concurrency**: AI workers sử dụng ThreadPoolExecutor (max_workers=10) cho xử lý song song
- **Session Management**: `disconectuser` text → xóa toàn bộ lịch sử chat của user
- **Soniox STT**: Sử dụng endpoint detection (max 1.5s silence) để xác định cuối câu
- **TTS Sentence Splitting**: Regex split by `.`, `!`, `?`, `…` rồi merge chunk <5 từ vào câu trước
- **Qdrant**: Collection `bytehome1`, vector size = 384, cosine distance, keyword index trên userId và groupId
- **Rate Limiting (Robot)**: Tối đa 1 request mỗi 5 giây từ robot client
- **Model loading**: OmniVoice TTS model được tải từ HuggingFace Hub về `AI_Service/tts_service/models/`

---

## 👨‍💻 Tác giả

**Duy Đỗ (doduy-AI)**
📧 dev.dinhduy@gmail.com
