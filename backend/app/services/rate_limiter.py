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
import math
import threading
import time
from typing import Callable, Deque, Dict, Optional, Tuple


class LoginRateLimiter:
    """
    Thread-safe sliding-window rate limiter tracking failed authentication attempts per client IP.

    Policy:
    - Maximum 5 failed attempts in any rolling 60-second window.
    - If >= 5 failed attempts exist within [now - 60, now], subsequent authentication
      attempts are denied with HTTP 429 Too Many Requests until the oldest failure in the
      window rolls past the 60-second boundary.
    - Retry-After indicates the exact number of seconds until the earliest relevant failure expires.
    - A successful authentication resets the failed attempt history for that client IP.
    - Uses time.monotonic() for robust, monotonic elapsed-time calculations unaffected by wall-clock shifts.
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
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for ip in stale_ips:
            self._attempts.pop(ip, None)
        self._last_cleanup = now

    def check_allowed(self, ip: str) -> Tuple[bool, int]:
        """
        Checks whether the client IP is permitted to attempt authentication.

        Returns:
            (is_allowed, retry_after_seconds)
            If is_allowed is False, retry_after_seconds is >= 1 based on when the oldest
            failure in the window expires.
        """
        with self._lock:
            now = self._clock()
            self._cleanup_expired_locked(now)
            timestamps = self._prune_ip_locked(ip, now)
            if len(timestamps) >= self.max_attempts:
                oldest_failure = timestamps[0]
                retry_after = max(1, math.ceil(oldest_failure + self.window_seconds - now))
                return False, retry_after
            return True, 0

    def record_failure(self, ip: str) -> Tuple[int, Optional[int]]:
        """
        Records a failed authentication attempt for the given IP address.

        Returns:
            (current_failure_count, retry_after_seconds_if_locked)
        """
        with self._lock:
            now = self._clock()
            self._cleanup_expired_locked(now)
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
        """Resets failed attempt tracking on successful authentication."""
        with self._lock:
            self._attempts.pop(ip, None)

    def reset(self):
        """Clears all rate limit tracking (for testing and administrative reset)."""
        with self._lock:
            self._attempts.clear()
            self._last_cleanup = self._clock()


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60.0)
