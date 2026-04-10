
from .chucking.router import smart_chuck_domain as chucking_router
from .clear_data.router import process_folder_to_markdown as clear_data_router
import os 
import json
import sys
from embetdding_service.redis_manager import redis_manager
from pathlib import Path
import shutil
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def worker_process_task(folder_path: str, title: str , folder_path_clean : str, u_id: str, groupId: str , base: str):
    print("--- ĐANG BẮT ĐẦU CLEAR DATA ---")
    clear_data_router(folder_path,folder_path_clean)
    print("--- CLEAR DATA XONG. BẮT ĐẦU CHUNKING ---")
    chucking_router(folder_path_clean,title,u_id,groupId,base)


def main():
    while True:
        task_data = redis_manager.listen_tasks("embedding_tasks")
        print(task_data)
        try:
            message = task_data[1]
            data = json.loads(message)
            base = data.get("base")
            u_id = data.get("userId")
            groupId = data.get("groupId")

            if u_id:
                print(f"Bắt đầu xử lý task Embedding cho User: {u_id}")
                src_dir = BASE_DIR / "uploads" / u_id
                folder_path_clean = BASE_DIR / "clean" / u_id
                dest_dir = BASE_DIR / "processed" 
                dest_dir.mkdir(parents=True, exist_ok=True)
                folder_path_clean.mkdir(parents=True, exist_ok=True)


                worker_process_task(src_dir,"BHXH",folder_path_clean,u_id, groupId,base)
                folder_path_clean_process = dest_dir / "clear" /u_id
                folder_path_clean_process.mkdir(parents=True, exist_ok=True)
                folder_path_uploads_process = dest_dir / "uploads" /u_id
                folder_path_uploads_process.mkdir(parents=True, exist_ok=True)


                for file in src_dir.iterdir():
                    if file.is_file():
                        shutil.move(str(file), dest_dir  / file.name)
                for file in folder_path_clean.iterdir():
                    if file.is_file():
                        shutil.move(str(file),folder_path_clean_process  / file.name)
                    
                    print(f" Hoàn thành xử lý cho {u_id}")
        except Exception  as e : 
            print(f"Lỗi khi xử lý task ",e)



if __name__ == "__main__":
    main()
    