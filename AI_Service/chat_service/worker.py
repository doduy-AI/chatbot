import json , os , sys
from redis_manager import redis_manager

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.config import settings


from concurrent.futures import ThreadPoolExecutor
from ai_engine import AIEngine 
executor = ThreadPoolExecutor(max_workers=10)
ai = AIEngine() 


def handle_task(data):
    user_id = data.get("userId")
    text = data.get("text")
    group_id = data.get("groupId")
    voice = data.get("voice")

    reply = ai.generate_respone(text, user_id, group_id)
    print("[BYTEHOME]", reply)

    redis_manager.publish("tts_tasks", {
        "userId": user_id,
        "reply": reply,
        "voice": voice,
        "status": "success"
    })
    print(f" Đã trả lời {user_id}")

def main():
    print(" sẵn sàng")
    print('[MODEL]', settings.MODEL_NAME)

    while True:
        task_data = redis_manager.listen_tasks("ai_tasks")
        if task_data:
            data = json.loads(task_data[1])
            executor.submit(handle_task, data)


if __name__ == "__main__":
    main()
