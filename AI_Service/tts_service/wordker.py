from fastapi import FastAPI , HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
import json , os , struct , threading , time , queue , asyncio
from concurrent.futures import ThreadPoolExecutor
import struct
import threading
import time
import queue
import asyncio
from redis_manager import redis_manager
from tts_service import generate_tts 
from config import settings

EXTERNAL_HOST = settings.EXTERNAL_HOST
EXTERNAL_PORT = settings.EXTERNAL_PORT
MAX_WORKERS = settings.MAX_WORKERS
QUEUE_MAXSIZE = settings.QUEUE_MAXSIZE
STREAM_GET_TIMEOUT = settings.STREAM_GET_TIMEOUT
QUEUE_PUT_TIMEOUT = settings.QUEUE_PUT_TIMEOUT

app = FastAPI()

audio_buffers = {}

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def create_wav_header(sample_rate=24000, bits_per_sample=16, channels=1):
    o = bytes("RIFF", "ascii")
    o += struct.pack("<I", 0)  # Sửa từ 0xFFFFFFFF thành 0
    o += bytes("WAVE", "ascii")
    o += bytes("fmt ", "ascii")
    o += struct.pack("<I", 16)
    o += struct.pack("<H", 1)
    o += struct.pack("<H", channels)
    o += struct.pack("<I", sample_rate)
    o += struct.pack("<I", sample_rate * channels * bits_per_sample // 8)
    o += struct.pack("<H", channels * bits_per_sample // 8)
    o += struct.pack("<H", bits_per_sample)
    o += bytes("data", "ascii")
    o += struct.pack("<I", 0)  # Sửa từ 0xFFFFFFFF thành 0
    return o

@app.get("/stream-voice/{task_id}")
async def stream_voice(task_id: str):
    async def stream_generator():
        q = audio_buffers.get(task_id)
        if not q:
            raise HTTPException(status_code=404, detail="task not found")
        yield create_wav_header()
        loop = asyncio.get_event_loop()
        while True:
            try:
                chunk = await loop.run_in_executor(None, lambda: q.get(timeout=STREAM_GET_TIMEOUT))
            except queue.Empty:
                print(f"[WARN] Stream {task_id} timeout, đóng stream.")
                break
            if chunk == "DONE":
                break
            if isinstance(chunk, bytes):
                yield chunk
        audio_buffers.pop(task_id, None)

    return StreamingResponse(stream_generator(), media_type="audio/wav")

def process_tts_task(user_id, text, task_id, q: queue.Queue):
    """Chạy generate_tts trong thread riêng và đẩy chunk vào q"""
    start_time = time.time()
    print(f"[TTS] Bắt đầu task {task_id} cho user {user_id}")

    try:
        first_chunk = True
        for chunk in generate_tts(text):
            if first_chunk:
                print(f"⏱ Task {task_id}: chunk đầu sau {time.time() - start_time:.2f}s")
                first_chunk = False
            try:
                q.put(chunk, timeout=QUEUE_PUT_TIMEOUT)
            except queue.Full:
                # Nếu queue đầy: log và bỏ chunk (không block cả worker)
                print(f"[WARN] Queue {task_id} đầy, bỏ chunk.")
                continue

        # Đánh dấu kết thúc
        try:
            q.put("DONE", timeout=QUEUE_PUT_TIMEOUT)
        except queue.Full:
            # Nếu queue vẫn đầy, cố gắng pop một lần trước khi đặt DONE
            print(f"[WARN] Queue {task_id} full khi đặt DONE. Thử xóa...")
            # không cố gắng nhiều, client sẽ timeout sau STREAM_GET_TIMEOUT

        print(f"[TTS] ✅ Xong task {task_id} ({time.time() - start_time:.2f}s)")
        redis_manager.publish(
            f"voice_ready:{user_id}",
            json.dumps({"type": "AI_VOICE_DONE", "taskId": task_id}),
        )

    except Exception as e:
        print(f"[ERR] Task {task_id}: {e}")
        try:
            q.put("DONE", timeout=QUEUE_PUT_TIMEOUT)
        except Exception:
            pass

def redis_listener():
    print("👂 Worker đang lắng nghe kênh tts_tasks...")
    while True:
        try:
            task_data = redis_manager.listen_tasks("tts_tasks")
            if not task_data:
                continue

            data = json.loads(task_data[1])
            user_id = data.get("userId")
            text = data.get("reply", "")
            task_id = f"task_{int(time.time() * 1000)}"

            # Tạo queue cho task và lưu vào audio_buffers trước khi publish URL
            q = queue.Queue(maxsize=QUEUE_MAXSIZE)
            audio_buffers[task_id] = q

            voice_url = f"http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/stream-voice/{task_id}"
            print(voice_url)
            # Gửi thông báo cho client
            redis_manager.publish(f"voice_ready:{user_id}", {
                "type": "AI_VOICE_REPLY",
                "text": text,
                "audioUrl": voice_url
            })

            # Submit task cho thread pool
            executor.submit(process_tts_task, user_id, text, task_id, q)

        except Exception as e:
            print(f"[ERR] Redis listener: {e}")

@app.on_event("startup")
async def startup_event():
    t = threading.Thread(target=redis_listener, daemon=True)
    t.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)