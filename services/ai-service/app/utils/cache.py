import redis
import os
import json

class Cache:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str):
        try:
            val = self.client.get(key)
            return json.loads(val) if val else None
        except:
            return None

    def set(self, key: str, value, ttl: int = 3600):
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except:
            pass
