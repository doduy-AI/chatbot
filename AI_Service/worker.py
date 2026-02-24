import json
from redis_manager import redis_manager
from config import settings


def main():
    print('[MODEL] ' , settings.MODEL_NAME)
    while True:
        task_data = redis_manager.listen_tasks("ai_tasks")
        print(task_data)
        if task_data:
            raw_json = task_data[1]
            data = json.loads(raw_json)
            
            # 3. Trích xuất các trường bạn cần
            user_id = data.get("userId")
            text = data.get("text")
            language = data.get("language")
            
            # In ra kiểm tra
            print(f"--- Nhận Task Mới ---")
            print(f" User: {user_id}")
            print(f" Text: {text}")
            print(f" Lang: {language}")
            print(f"----------------------")

if __name__ == "__main__":
    main()
