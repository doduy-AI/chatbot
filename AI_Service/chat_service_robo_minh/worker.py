import json 
import time
from chat_service_robo_minh.redis_manager import redis_manager
from config.config import settings
from concurrent.futures import ThreadPoolExecutor
from chat_service_robo_minh.ai_engine import AIEngine 
executor = ThreadPoolExecutor(max_workers=10)
ai = AIEngine() 


def handle_task(data):
    userId = data.get("userId")
    text = data.get("text")
    group_id = data.get("groupId")
    voice = data.get("voice")
    service = data.get("service")
    audio_format = data.get("audio_format")
    if text == "disconectuser":
        ai.clear_session(userId)
        return
    prompt = redis_manager.get_cache(f"group:{group_id}:content")
    print(prompt)
    strart_time = time.time()
    reply = ai.generate_respone(text,prompt ,userId, group_id)
    print(f"[CHAT_Service] time {time.time() - strart_time} ")
    if (service):
            redis_manager.publishChat("chat-respone", {
            "userId": userId,
            "reply": reply,
            "status": "success"
        })
    else:
        redis_manager.publish("tts_tasks", {
            "userId": userId,
            "reply": reply,
            "voice": voice,
            "audio_format":audio_format,
            "status": "success"
        })

def main():
    print(" sẵn sàng")
    print('[MODEL]', settings.MODEL_NAME)

    while True:
        task_data = redis_manager.listen_tasks("ai_tasks")
        print(task_data)
            
        if task_data:
            data = json.loads(task_data[1])
            executor.submit(handle_task, data)


if __name__ == "__main__":
    main()
