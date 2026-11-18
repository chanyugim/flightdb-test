from collections import OrderedDict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

from app.core.config import get_settings


class RequestLimiter:
    def __init__(self):
        self.clients = OrderedDict()
        self.lock = Lock()

    def allow(self, key: str, limit: int) -> bool:
        current = monotonic()
        with self.lock:
            while (
                self.clients and next(iter(self.clients.values()))[-1] <= current - 60
            ):
                self.clients.popitem(last=False)
            entries = self.clients.get(key)
            if entries is None:
                if len(self.clients) >= 10000:
                    return False
                entries = deque()
                self.clients[key] = entries
            while entries and entries[0] <= current - 60:
                entries.popleft()
            if len(entries) >= limit:
                return False
            entries.append(current)
            self.clients.move_to_end(key)
            return True


sensitive_limiter = RequestLimiter()


def limit_sensitive_requests(request: Request):
    client = request.client.host if request.client else "unknown"
    if not sensitive_limiter.allow(
        client, get_settings().sensitive_requests_per_minute
    ):
        raise HTTPException(429, "Too many requests", headers={"Retry-After": "60"})
