import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from embetdding_service.redis_manager import redis_manager
from embetding_engine import process_embedding_for_user


def main():
  
    while True:
        
        task_data = redis_manager.listen_tasks("embedding_tasks")
        print(task_data)
        if task_data:
            try:
                topic, message = task_data
                # print("[topic] "+ topic)
                # print('[message]'+ message)
                data = json.loads(message)
                u_id = data.get("userId")
                # print(u_id)
                if u_id:
                    print(f" Nhận yêu cầu Embedding cho User: {u_id}")
                    
                   
                    process_embedding_for_user(u_id)
                    
                    print(f" Hoàn thành xử lý cho {u_id}")
                else:
                    print(" Task không hợp lệ (thiếu userId)")

            except Exception as e : 
                print(f"Lỗi khi xử lý task",e)
       


if __name__ == "__main__":
    main()