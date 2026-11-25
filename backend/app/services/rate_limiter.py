"""
Rate Limiting & Brute-Force Protection Service for AI GrowthPilot.

Provides thread-safe in-memory failure tracking and cooldown enforcement
to protect authentication endpoints against credential stuffing and brute-force attacks.
"""
import time
import threading
from typing import Dict, Tuple, Optional


class LoginRateLimiter:
    """
    In-memory rate limiter tracking consecutive failed authentication attempts per IP address.
    Enforces lockout windows after exceeding max_attempts.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        lockout_duration_seconds: int = 60,
        cleanup_interval_seconds: int = 300
    ):
        self.max_attempts = max_attempts
        self.lockout_duration_seconds = lockout_duration_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._lock = threading.Lock()
        # IP -> {"failures": int, "lockout_until": float, "last_attempt": float}
        self._attempts: Dict[str, Dict[str, float]] = {}
        self._last_cleanup = time.time()

    def _cleanup_expired(self, now: float):
        if now - self._last_cleanup > self.cleanup_interval_seconds:
            expired_ips = [
                ip for ip, data in self._attempts.items()
                if now > data.get("lockout_until", 0) and (now - data.get("last_attempt", 0)) > 3600
            ]
            for ip in expired_ips:
                del self._attempts[ip]
            self._last_cleanup = now

    def check_allowed(self, ip: str) -> Tuple[bool, int]:
        """
        Checks whether the IP is permitted to attempt authentication.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            self._cleanup_expired(now)
            record = self._attempts.get(ip)
            if not record:
                return True, 0
            lockout_until = record.get("lockout_until", 0.0)
            if now < lockout_until:
                retry_after = int(lockout_until - now) + 1
                return False, retry_after
            return True, 0

    def record_failure(self, ip: str) -> Tuple[int, Optional[int]]:
        """
        Records a failed authentication attempt.
        Returns (current_failures, lockout_duration_if_locked).
        """
        now = time.time()
        with self._lock:
            self._cleanup_expired(now)
            record = self._attempts.setdefault(ip, {"failures": 0, "lockout_until": 0.0, "last_attempt": now})
            # If previous lockout expired, reset failures
            if now > record["lockout_until"] and record["failures"] >= self.max_attempts:
                record["failures"] = 0
                record["lockout_until"] = 0.0

            record["failures"] += 1
            record["last_attempt"] = now
            if record["failures"] >= self.max_attempts:
                record["lockout_until"] = now + self.lockout_duration_seconds
                return record["failures"], self.lockout_duration_seconds
            return record["failures"], None

    def record_success(self, ip: str):
        """Resets failed attempt tracking on successful authentication."""
        with self._lock:
            if ip in self._attempts:
                del self._attempts[ip]

    def reset(self):
        """Clears all rate limit tracking (useful for testing)."""
        with self._lock:
            self._attempts.clear()


login_rate_limiter = LoginRateLimiter(max_attempts=5, lockout_duration_seconds=60)
