"""Token Bucket Rate Limiter for upstream regulator politeness."""

import threading
import time


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket rate limiter ensuring politeness to regulator servers."""

    def __init__(self, rate_per_second: float = 0.5, burst_capacity: int = 2) -> None:
        self.rate = rate_per_second
        self.capacity = burst_capacity
        self.tokens = float(burst_capacity)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now

                # Replenish tokens based on elapsed time
                self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

                # Calculate sleep duration needed for next token
                needed = (1.0 - self.tokens) / self.rate

            time.sleep(max(0.05, needed))
