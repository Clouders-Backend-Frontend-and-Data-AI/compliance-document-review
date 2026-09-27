"""Simple in-process rate limiter for auth/upload abuse protection."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import settings

_lock = Lock()
_buckets: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request, bucket: str, limit: int, window_seconds: int = 60) -> None:
    if not settings.ENABLE_RATE_LIMITING:
        return
    if settings.ENVIRONMENT.lower() == "test":
        return

    key = (bucket, _client_ip(request))
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for '{bucket}'. Try again shortly.",
            )
        q.append(now)
