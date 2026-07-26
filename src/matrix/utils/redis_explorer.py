"""Print Redis keys — Operator console for Matrix session / checkpoints."""

import json

from matrix.services.redis_client import redis_client


def explore_redis() -> None:
    print("=" * 80)
    print("Redis Keys (Matrix / Operator)")
    print("=" * 80)

    for key in redis_client.scan_iter("*"):
        print(f"\nKey : {key}")
        key_type = redis_client.type(key)
        print(f"Type: {key_type}")

        if key_type == "string":
            value = redis_client.get(key)
            try:
                print(json.dumps(json.loads(value), indent=4))
            except Exception:
                print(value)
        elif key_type == "hash":
            print(json.dumps(redis_client.hgetall(key), indent=4))
        elif key_type == "list":
            print(redis_client.lrange(key, 0, -1))
        elif key_type == "set":
            print(list(redis_client.smembers(key)))
        elif key_type == "zset":
            print(redis_client.zrange(key, 0, -1, withscores=True))


def main() -> None:
    explore_redis()


if __name__ == "__main__":
    main()
