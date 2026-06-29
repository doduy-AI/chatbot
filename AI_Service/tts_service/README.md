# 🗣️ TTS Service — Text-to-Speech Streaming

## 📌 Tổng quan

`tts_service` là dịch vụ chuyển văn bản thành giọng nói (TTS) sử dụng **BytehmeTTS** model — một model voice cloning tự host. Dịch vụ nhận text từ Redis queue `tts_tasks`, sinh audio streaming theo thời gian thực, và public URL cho client truy cập qua **FastAPI StreamingResponse**.

## 🔄 Luồng hoạt động

```
Redis Queue "tts_tasks"
       │
       ▼
  wordker.py (async main loop)
       │ BRPOP
       ▼
  redis_listener()
       │
       ├─► Tạo task_id và Audio Queue (asyncio.Queue)
       ├─► Publish voice_ready:{userId} → Redis (chứa audioUrl)
       │
       └─► process_tts_task(userId, text, taskId, queue, voice, audioFormat)
              │
              ├─► run_tts() trong ThreadPoolExecutor (sync code)
              │     ├─► split_sentences(text): Chia text thành chunk ≤30 từ
              │     ├─► BytehmeTTS.generate(text, ref_audio, ref_text)
              │     ├─► float_to_pcm_bytes() hoặc lameenc MP3 encode
              │     └─► Yield từng audio chunk → asyncio.Queue
              │
              └─► Push "DONE" → queue (kết thúc stream)

Client request:
  GET /stream-voice/{task_id}?audio_format=mp3
       │
       ▼
  stream_generator() → StreamingResponse (audio/mpeg hoặc audio/octet-stream)
```

## 📂 Cấu trúc thư mục

```
tts_service/
├── wordker.py              # FastAPI app + Redis listener + streaming endpoint
├── tts_service.py          # BytehmeTTS TTS engine wrapper + audio processing
├── dowload_model.py        # HuggingFace model downloader
├── Dockerfile              # Docker image
├── docker-compose.yaml     # Docker Compose config
├── pyproject.toml          # UV project config
├── uv.lock                 # UV lock file
├── .env                    # Environment variables
├── config/
│   ├── config.py           # TTS settings (Pydantic)
│   └── redis_maneger.py    # Redis client
├── input/
│   └── voice_profiles.py   # Voice definitions + HuggingFace audio download
├── models/                 # BytehmeTTS model weights (gitignored)
├── BytehmeTTS/              # BytehmeTTS TTS library (~30 Python files)
│   ├── cli/                # CLI: train, infer, demo, infer_batch
│   ├── data/               # Data processing: batching, dataset, collator
│   ├── eval/               # Evaluation: MOS, WER, speaker similarity
│   ├── models/             # BytehmeTTS model architecture
│   ├── scripts/            # Audio utilities: denoise, extract tokens
│   ├── training/           # Training pipeline: builder, trainer, checkpoint
│   └── utils/              # Audio, text, voice design, duration utils
└── output/                 # Audio output (gitignored)
```

## 🎤 Voice Profiles

| Profile ID | Mô tả | Ref Audio | Ref Text |
|------------|-------|-----------|----------|
| `nutrem` | Giọng trẻ em, thân thiện | `nutrem.wav` (HuggingFace) | "Xin chào, mình là robot Chiko..." |
| `nuhanoi` | Giọng nữ Hà Nội, chuyên nghiệp | `giongnuhanoi6s.wav` (HuggingFace) | "Xin chào, tôi là một người yêu thích công nghệ..." |
| `nam` | Giọng nam | `nam.wav` (HuggingFace) | "Đây là câu chuyện về một trong những vụ gian lận..." |

Audio reference được tự động tải từ HuggingFace repo `doduy1911/audio_TTS` khi chạy lần đầu.

## 🔧 Xử lý Audio

### Sentence Splitting (`split_sentences`)
```python
Input:  "Hello. This is a very long sentence with many words..."
        ↓ regex split by [.!?…]
        ↓ split by [,;:] if > 30 words
        ↓ merge chunk < 5 words vào câu trước
Output: ["Hello.", "This is a very long sentence", "with many words..."]
```

### Audio Output Formats

| Format | Encoder | Sample Rate | Output |
|--------|---------|-------------|--------|
| `wav` (default) | PCM 16-bit int | 24kHz | Raw PCM bytes |
| `mp3` | lameenc 128kbps | 24kHz → mono | MP3 frames |

### Fade In/Out
- 50ms fade-in ở đầu mỗi chunk
- 50ms fade-out ở chunk cuối cùng

## 🌐 API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/stream-voice/{task_id}` | GET | Stream audio theo task (query: `?audio_format=mp3`) |

### Response Headers (MP3):
```
Content-Type: audio/mpeg
X-Accel-Buffering: no
Cache-Control: no-cache, no-store, must-revalidate
Connection: keep-alive
```

## 🚀 Cách chạy

```bash
cd AI_Service/tts_service

# Cài đặt dependencies
uv sync

# Chạy service (port từ biến PORT trong .env)
uv run wordker.py
```

## 📦 Dependencies chính
- `torch` — PyTorch (CUDA nếu có, fallback CPU)
- `BytehmeTTS` — BytehmeTTS TTS model (local library)
- `fastapi` + `uvicorn` — HTTP server + streaming
- `lameenc` — MP3 encoding
- `huggingface_hub` — Download models & voice references
- `redis` — Message queue
- `numpy` — Audio processing

## ⚙️ Biến môi trường

| Biến | Mô tả | Default |
|------|-------|---------|
| `PORT` | FastAPI server port | — |
| `EXTERNAL_HOST` | Public URL prefix cho audio stream | `localhost:8001` |
| `MODEL_NAME` | HuggingFace repo ID cho BytehmeTTS model | — |
| `TOKEN_HF` | HuggingFace API token | — |
| `QUEUE_MAXSIZE` | Max size của asyncio audio queue | — |
| `STREAM_GET_TIMEOUT` | Timeout chờ audio chunk (giây) | — |
| `QUEUE_PUT_TIMEOUT` | Timeout push audio chunk (giây) | — |
| `REDIS_HOST` / `REDIS_PORT` / `PASS_REDIS` | Redis connection | — |

## ⚠️ Ghi chú

- Model BytehmeTTS nặng, cần GPU (CUDA) để chạy nhanh. Trên CPU sẽ chậm.
- Lần chạy đầu tiên sẽ tự động tải model từ HuggingFace (~vài GB).
- Audio queue dùng `asyncio.Queue` với maxsize để tránh memory overflow.
- Service tự khởi động `redis_listener()` background task khi FastAPI startup.
