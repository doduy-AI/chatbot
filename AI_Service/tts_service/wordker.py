from tts_service import generate_tts_stream
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from config.config import settings
from config.redis_maneger import redis_manager
import uvicorn
import os
import time
import io
import asyncio
import json
STREAM_GET_TIMEOUT = settings.STREAM_GET_TIMEOUT
EXTERNAL_HOST = settings.EXTERNAL_HOST
QUEUE_MAXSIZE = settings.QUEUE_MAXSIZE

app = FastAPI()
audio_buffers = {}

@app.get("/stream-voice/{task_id}")
async def stream_voice(task_id: str):
    async def stream_generator():
        q = audio_buffers.get(task_id)
        if not q:
            return

        while True:
            try:
                chunk = await asyncio.wait_for(q.get(), timeout=STREAM_GET_TIMEOUT)
                if chunk == "DONE":
                    break
                if isinstance(chunk, bytes):
                    yield chunk
            except:
                break
        audio_buffers.pop(task_id, None)

    return StreamingResponse(stream_generator(), media_type="audio/mpeg") 


async def process_tts_task(user_id, text, task_id, q: asyncio.Queue, voice):
    loop = asyncio.get_event_loop()
    start_time = time.time()
    print(f"[TTS] Bắt đầu task {task_id} cho user {user_id}")

    try:
        first_chunk = True
        def run_tts():
            nonlocal first_chunk
            for chunk in generate_tts_stream(text, voice):  # ✅ đổi tên
                if first_chunk:
                    print(f"  ⏱ Task {task_id}: chunk đầu sau {time.time() - start_time:.2f}s")
                    first_chunk = False
                future = asyncio.run_coroutine_threadsafe(q.put(chunk), loop)
                future.result(timeout=30)

        await loop.run_in_executor(None, run_tts)
        await q.put("DONE")
        redis_manager.publish(
            f"voice_ready:{user_id}",
            json.dumps({"type": "AI_VOICE_DONE", "taskId": task_id}),
        )

    except Exception as e:
        print(f"[ERR] Task {task_id}: {e}")
        await q.put("DONE")



async def redis_listener():
    print(" Worker đang lắng nghe kênh tts_tasks...")
    loop = asyncio.get_event_loop()

    while True:
        try:
            task_data = await loop.run_in_executor(
                None, lambda: redis_manager.listen_tasks("tts_tasks")
            )
            if not task_data:
                continue

            data = json.loads(task_data[1])
            user_id = data.get("userId")
            text = data.get("reply", "")
            voice = data.get("voice")
            task_id = f"task_{int(time.time() * 1000)}"

            # Tạo queue cho task và lưu vào audio_buffers trước khi publish URL
            q = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
            audio_buffers[task_id] = q

            voice_url = f"{EXTERNAL_HOST}/stream-voice/{task_id}"
            print(voice_url)
            # Gửi thông báo cho client
            redis_manager.publish(f"voice_ready:{user_id}", {
                "type": "AI_VOICE_REPLY",
                "text": text,
                "audioUrl": voice_url
            })

            # Submit task cho thread pool
            await process_tts_task(user_id, text, task_id, q,voice)

        except Exception as e:
            print(f"[ERR] Redis listener: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)

