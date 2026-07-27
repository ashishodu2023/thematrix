import os
from urllib.parse import urlparse

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_parsed = urlparse(REDIS_URL)
_host = _parsed.hostname or "localhost"
_port = int(_parsed.port or 6379)
_db = int((_parsed.path or "/0").lstrip("/") or 0)

redis_client = redis.Redis(
    host=_host,
    port=_port,
    db=_db,
    decode_responses=True,
)
