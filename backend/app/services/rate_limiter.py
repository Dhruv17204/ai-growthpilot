"""
Rate Limiting & Brute-Force Protection Service for AI GrowthPilot.

Implements an in-memory sliding-window failure tracker to defend authentication
endpoints against brute-force password guessing and credential stuffing attacks.

Architecture & Concurrency Note:
This in-memory implementation relies on process-local state synchronized via threading.Lock.
It is strictly suitable for single-process deployments (such as the default single-instance
container deployment). In multi-worker environments (e.g. Gunicorn/Uvicorn with multiple workers)
or distributed horizontal clusters behind a load balancer, rate-limiting state must be shared
across processes using an external distributed store such as Redis or Memcached.
"""
import collections
import contextlib
import math
import threading
import time
from typing import Callable, Deque, Dict, Iterator, Optional, Tuple


class AttemptSlot:
    """
    Handle for an in-flight login attempt.
    Tracks whether the attempt was finalized as a success, failure, or released.
    Guarantees that in-flight capacity is released exactly once.
    """

    def __init__(self, limiter: "LoginRateLimiter", ip: str):
        self._limiter = limiter
        self._ip = ip
        self._finalized = False

    def mark_success(self):
        """Finalizes the in-flight attempt as a successful authentication."""
        if not self._finalized:
            self._finalized = True
            self._limiter.record_success(self._ip)

    def mark_failure(self) -> Tuple[int, Optional[int]]:
        """Finalizes the in-flight attempt as a failed authentication."""
        if not self._finalized:
            self._finalized = True
            return self._limiter.record_failure(self._ip)
        return self._limiter.failure_count(self._ip), None

    def release(self):
        """Releases the in-flight slot without recording a success or failure."""
        if not self._finalized:
            self._finalized = True
            self._limiter.release_in_flight(self._ip)


class LoginRateLimiter:
    """
    Thread-safe sliding-window rate limiter tracking failed authentication attempts
    and active in-flight requests per client IP.

    Policy:
    - Maximum 5 failed or in-flight attempts in any rolling 60-second window.
    - If (failures_in_window + in_flight) >= 5, subsequent attempts are denied with
      HTTP 429 Too Many Requests until the oldest failure in the window rolls past
      the 60-second boundary (or active in-flight attempts complete).
    - Retry-After indicates the exact number of seconds until the earliest relevant
      failure in the rolling window expires.
    - A successful authentication resets the failed attempt history for that client IP.
    - In-flight tracking ensures that concurrent simultaneous requests cannot all pass
      an outdated check during parallel bursts.
    - Synchronized via threading.Lock using monotonic time (time.monotonic).

    Architecture & Concurrency Limitation:
    This in-memory implementation relies on process-local state synchronized via threading.Lock.
    It is strictly suitable for single-process deployments (such as the default single-instance
    container deployment). In multi-worker environments (e.g. Gunicorn/Uvicorn with multiple workers)
    or distributed horizontal clusters behind a load balancer, rate-limiting state must be shared
    across processes using an external distributed store such as Redis or Memcached.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: float = 60.0,
        cleanup_interval_seconds: float = 300.0,
        clock: Optional[Callable[[], float]] = None,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._clock = clock if clock is not None else time.monotonic
        self._lock = threading.Lock()
        # IP -> deque of failure timestamps (monotonic float)
        self._attempts: Dict[str, Deque[float]] = {}
        # IP -> count of currently in-flight login requests
        self._in_flight: Dict[str, int] = collections.defaultdict(int)
        self._last_cleanup = self._clock()

    def _prune_ip_locked(self, ip: str, now: float) -> Deque[float]:
        """Prunes timestamps older than the sliding window for a given IP. Caller must hold self._lock."""
        timestamps = self._attempts.get(ip)
        if timestamps is None:
            return collections.deque()
        cutoff = now - self.window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if not timestamps:
            self._attempts.pop(ip, None)
            return collections.deque()
        return timestamps

    def _cleanup_expired_locked(self, now: float):
        """Performs periodic bounded cleanup across all tracked IPs. Caller must hold self._lock."""
        if now - self._last_cleanup < self.cleanup_interval_seconds:
            return
        cutoff = now - self.window_seconds
        stale_ips = [
            ip for ip, timestamps in self._attempts.items()
            if (not timestamps or timestamps[-1] <= cutoff) and self._in_flight.get(ip, 0) == 0
        ]
        for ip in stale_ips:
            self._attempts.pop(ip, None)
            self._in_flight.pop(ip, None)
        self._last_cleanup = now

    def check_allowed(self, ip: str) -> Tuple[bool, int]:
        """
        Inspects whether the client IP is permitted to attempt authentication.
        Accounts for active in-flight attempts as well as failures in the rolling window.

        Returns:
            (is_allowed, retry_after_seconds)
            If is_allowed is False, retry_after_seconds is >= 1 based on when the oldest
            failure in the window expires.
        """
        with self._lock:
            now = self._clock()
            self._cleanup_expired_locked(now)
            timestamps = self._prune_ip_locked(ip, now)
            active_load = len(timestamps) + self._in_flight.get(ip, 0)
            if active_load >= self.max_attempts:
                if timestamps:
                    oldest_failure = timestamps[0]
                    retry_after = max(1, math.ceil(oldest_failure + self.window_seconds - now))
                else:
                    retry_after = max(1, math.ceil(self.window_seconds))
                return False, retry_after
            return True, 0

    def acquire(self, ip: str) -> Tuple[bool, int]:
        """
        Atomically checks rate limits and reserves an in-flight attempt slot for the client IP.

        Returns:
            (is_allowed, retry_after_seconds)
            If True, caller MUST finalize via record_failure(ip), record_success(ip),
            or release_in_flight(ip).
        """
        with self._lock:
            now = self._clock()
            self._cleanup_expired_locked(now)
            timestamps = self._prune_ip_locked(ip, now)
            active_load = len(timestamps) + self._in_flight.get(ip, 0)
            if active_load >= self.max_attempts:
                if timestamps:
                    oldest_failure = timestamps[0]
                    retry_after = max(1, math.ceil(oldest_failure + self.window_seconds - now))
                else:
                    retry_after = max(1, math.ceil(self.window_seconds))
                return False, retry_after
            self._in_flight[ip] = self._in_flight.get(ip, 0) + 1
            return True, 0

    @contextlib.contextmanager
    def attempt(self, ip: str) -> Iterator[Tuple[bool, int, AttemptSlot]]:
        """
        Context manager for concurrency-safe login attempt admission.
        Automatically manages in-flight reservation and ensures no slots are leaked.

        Yields:
            (is_allowed, retry_after, slot)
        """
        allowed, retry_after = self.acquire(ip)
        slot = AttemptSlot(self, ip)
        if not allowed:
            yield False, retry_after, slot
            return
        try:
            yield True, 0, slot
        finally:
            slot.release()

    def record_failure(self, ip: str) -> Tuple[int, Optional[int]]:
        """
        Records a failed authentication attempt for the given IP address
        and decrements its in-flight count if active.

        Returns:
            (current_failure_count, retry_after_seconds_if_locked)
        """
        with self._lock:
            now = self._clock()
            self._cleanup_expired_locked(now)
            if self._in_flight.get(ip, 0) > 0:
                self._in_flight[ip] -= 1
                if self._in_flight[ip] <= 0:
                    self._in_flight.pop(ip, None)

            timestamps = self._prune_ip_locked(ip, now)
            if ip not in self._attempts:
                self._attempts[ip] = timestamps
            timestamps.append(now)
            current_count = len(timestamps)
            if current_count >= self.max_attempts:
                oldest_failure = timestamps[0]
                retry_after = max(1, math.ceil(oldest_failure + self.window_seconds - now))
                return current_count, retry_after
            return current_count, None

    def record_success(self, ip: str):
        """
        Resets failed attempt tracking on successful authentication
        and decrements in-flight count if active.
        """
        with self._lock:
            if self._in_flight.get(ip, 0) > 0:
                self._in_flight[ip] -= 1
                if self._in_flight[ip] <= 0:
                    self._in_flight.pop(ip, None)
            self._attempts.pop(ip, None)

    def release_in_flight(self, ip: str):
        """Releases an in-flight reservation without recording a failure or success."""
        with self._lock:
            if self._in_flight.get(ip, 0) > 0:
                self._in_flight[ip] -= 1
                if self._in_flight[ip] <= 0:
                    self._in_flight.pop(ip, None)

    def in_flight_count(self, ip: str) -> int:
        """Returns the current number of in-flight attempts for the given IP."""
        with self._lock:
            return self._in_flight.get(ip, 0)

    def failure_count(self, ip: str) -> int:
        """Returns the current number of valid failed attempts in the sliding window."""
        with self._lock:
            now = self._clock()
            timestamps = self._prune_ip_locked(ip, now)
            return len(timestamps)

    def reset(self):
        """Clears all rate limit and in-flight tracking (for testing and administrative reset)."""
        with self._lock:
            self._attempts.clear()
            self._in_flight.clear()
            self._last_cleanup = self._clock()


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0)
