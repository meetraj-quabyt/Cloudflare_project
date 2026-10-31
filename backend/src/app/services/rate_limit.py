import time
from collections import defaultdict, deque

# In-process sliding window. Not globally consistent across serverless instances.
# Documented limitation: use Cloudflare Rate Limiting or Durable Objects for production.
_buckets: dict[str, deque] = defaultdict(deque)


def allow(key: str, limit: int = 60, window: int = 60) -> bool:
    now = time.time()
    q = _buckets[key]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True