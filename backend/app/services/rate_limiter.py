from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class InMemoryRateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int) -> tuple[bool, int]:
        if limit <= 0:
            return True, 0

        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] < cutoff:
                requests.popleft()

            remaining = max(limit - len(requests), 0)
            if remaining <= 0:
                return False, 0

            requests.append(now)
            return True, remaining - 1


def is_ai_cost_endpoint(method: str, path: str) -> bool:
    if method != "POST":
        return False
    return (
        path.endswith("/summaries")
        or path.endswith("/explanations")
        or path.endswith("/flashcards")
        or path.endswith("/quizzes")
        or path.endswith("/review-quiz")
        or path.endswith("/ocr")
    )
