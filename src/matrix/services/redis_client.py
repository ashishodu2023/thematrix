import redis

REDIS_URL = "redis://localhost:6379"

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)
