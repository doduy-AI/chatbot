import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from embetdding_service.redis_manager import redis_manager
from embetding_engine import process_embedding_for_user
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def main():
  
    while True:
        
        task_data = redis_manager.listen_tasks("embedding_tasks")
        print(task_data)
        if task_data:
            try:
                topic, message = task_data
                data = json.loads(message)
                base = data.get("base")
                u_id = data.get("userId")
                groupId = data.get("groupId")
                


                if u_id:
                    print(f" Nhận yêu cầu Embedding cho User: {u_id}")
                    
                    process_embedding_for_user(u_id, groupId, base)
                    
                    src_dir = BASE_DIR / "upload" / u_id
                    dest_dir = BASE_DIR / "processed" / u_id
                    
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    for file in src_dir.iterdir():
                        if file.is_file():
                            shutil.move(str(file), dest_dir / file.name)
                    
                    print(f" Hoàn thành xử lý cho {u_id}")
                else:
                    print(" Task không hợp lệ (thiếu userId)")

            except Exception as e : 
                print(f"Lỗi khi xử lý task",e)
       


if __name__ == "__main__":
    main()