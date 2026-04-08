# from .clear_data.router import  router as clear_data_router
# from .clear_data.classifier import  router as clear_data_router

from .chucking.router import smart_chuck_domain as chucking_router
from .clear_data.router import process_folder_to_markdown as clear_data_router
import os 

def worker_process_task(folder_path: str, title: str , folder_path_clean : str):
    print("--- ĐANG BẮT ĐẦU CLEAR DATA ---")
    clear_data_router(folder_path,folder_path_clean)
    print("--- CLEAR DATA XONG. BẮT ĐẦU CHUNKING ---")
    chucking_router(folder_path_clean,title)


if __name__ == "__main__":
    worker_process_task("/home/doduy/Downloads/audio_test","BHXH","/home/doduy/Downloads/audio_test/abc")