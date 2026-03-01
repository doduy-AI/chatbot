from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import json , os
import struct
import threading
import time
import queue
import asyncio
from redis_manager import redis_manager
from tts_service import generate_tts 
EXTERNAL_HOST = os.getenv("EXTERNAL_HOST", "127.0.0.1")
EXTERNAL_PORT = os.getenv("EXTERNAL_PORT", "8080")
app = FastAPI()

audio_buffers = {}

def create_wav_header(sample_rate=24000, bits_per_sample=16, channels=1):
    o = bytes("RIFF", 'ascii')
    o += struct.pack('<I', 36 + 10000000) 
    o += bytes("WAVE", 'ascii')
    o += bytes("fmt ", 'ascii')
    o += struct.pack('<I', 16)
    o += struct.pack('<H', 1) 
    o += struct.pack('<H', channels)
    o += struct.pack('<I', sample_rate)
    o += struct.pack('<I', sample_rate * channels * bits_per_sample // 8)
    o += struct.pack('<H', channels * bits_per_sample // 8)
    o += struct.pack('<H', bits_per_sample)
    o += bytes("data", 'ascii')
    o += struct.pack('<I', 10000000)
    return o

@app.get("/stream-voice/{task_id}")
async def stream_voice(task_id: str):
    async def stream_generator():
        q = audio_buffers.get(task_id)
        if not q:
            return

        yield create_wav_header()
        
        loop = asyncio.get_event_loop()
        while True:
            chunk = await loop.run_in_executor(None, q.get)
            
            if chunk == "DONE":
                break
            
            if isinstance(chunk, bytes):
                yield chunk
            else:
                continue
        
        if task_id in audio_buffers:
            del audio_buffers[task_id]

    return StreamingResponse(stream_generator(), media_type="audio/wav")

def redis_listener():
    print(" Worker đang lắng nghe tts_tasks trên Redis...")
    while True:
        try:
            task_data = redis_manager.listen_tasks("tts_tasks")
            if not task_data:
                continue

            data = json.loads(task_data[1])
            user_id = data.get("userId")
            text = data.get("reply", "")
            task_id = f"task_{int(time.time()*1000)}"

            q = queue.Queue()
            audio_buffers[task_id] = q

            voice_url = f"http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/stream-voice/{task_id}"
            print(f" URL: {voice_url}")
            result = {
                "text" : text ,
                "url" : voice_url
            }
            redis_manager.publish(f"voice_ready:{user_id}",result)
            start_time = time.time()
            first = True
            for chunk in generate_tts(text):
                if first:
                    print(f"⏱ Chunk đầu: {time.time() - start_time:.2f}s")
                    print(f"DEBUG: Nhận được chunk dung lượng {len(chunk)} bytes") # Thêm dòng này
                    first = False
                q.put(chunk)
            
            q.put("DONE")
            print(f"Xong {task_id}")

        except Exception as e:
            print(f" Lỗi: {e}")

@app.on_event("startup")
async def startup_event():
    t = threading.Thread(target=redis_listener, daemon=True)
    t.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)