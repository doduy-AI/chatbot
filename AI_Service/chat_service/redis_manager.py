import redis
import json
import os
import  sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import settings

class RedisManager:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    def listen_tasks(self, queue_name):
        return self.client.brpop(queue_name, timeout=0)

    def publish(self, channel, data):
        self.client.lpush(channel, json.dumps(data))  
    
    def publishChat(self, channel, data):
        self.client.publish(channel, json.dumps(data))  
        
    def get_cache(self, key):
        data = self.client.get(key)
        return data if data else None
redis_manager = RedisManager()