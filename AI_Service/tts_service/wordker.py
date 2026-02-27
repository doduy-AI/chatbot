from redis_manager import redis_manager


def main():
    print("tts service")
    while True: 
        task_data = redis_manager.listen_tasks("tts_tasks")
        print(task_data)


if __name__ == "__main__":
    main()
