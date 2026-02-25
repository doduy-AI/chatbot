import json
from redis_manager import redis_manager
from config import settings


def main():
  
    while True:
        
        task_data = redis_manager.listen_tasks("ai_tasks")
        print(task_data)
       


if __name__ == "__main__":
    main()
