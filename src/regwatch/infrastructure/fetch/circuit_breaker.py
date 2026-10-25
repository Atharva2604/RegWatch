"""Circuit Breaker pattern to protect against failing upstream regulators."""

import threading
import time
from enum import Enum
from regwatch.domain.errors import CircuitBreakerOpenError


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Stateful circuit breaker that trips after N consecutive failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_state_change = time.monotonic()
        self.lock = threading.Lock()

    def before_call(self) -> None:
        with self.lock:
            now = time.monotonic()
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Upstream recovery window active ({self.recovery_timeout}s)."
                    )

    def on_success(self) -> None:
        with self.lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED

    def on_failure(self) -> None:
        with self.lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = time.monotonic()
