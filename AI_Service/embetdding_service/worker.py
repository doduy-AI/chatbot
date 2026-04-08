# from .clear_data.router import  router as clear_data_router
# from .clear_data.classifier import  router as clear_data_router

from .chucking.router import smart_chuck_domain as chucking_router
import os 

def worker_process_task(task_id: str, title: str):
    forder_path = task_id
    chucking_router(forder_path,title)


if __name__ == "__main__":
    worker_process_task("abc","BHXH")