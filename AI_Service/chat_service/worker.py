import json , os , sys
from redis_manager import redis_manager

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.config import settings

from ai_engine import AIEngine 


def main():
    ai = AIEngine()
    print("sẵn sàng")
    print('[MODEL] ' , settings.MODEL_NAME)
    while True:
        task_data = redis_manager.listen_tasks("ai_tasks")
        print(task_data)
        if task_data:
            raw_json = task_data[1]
            data = json.loads(raw_json)
            # print(data)
            
            # 3. Trích xuất các trường bạn cần
            user_id = data.get("userId")
            text = data.get("text")
            language = data.get("language")

            # fix cứng group_id
            group_id = data.get("groupId")
            voice = data.get("voice")
            
            reply = ai.generate_respone(text ,user_id,group_id)
            print("[BYTEHOME]" , reply)
            result = {
                "userId": user_id,
                "reply": reply,
                "voice":voice,
                "status": "success"
            }
            redis_manager.publish("tts_tasks", result)
            print(f"✅ Đã trả lời {user_id}")


if __name__ == "__main__":
    main()
