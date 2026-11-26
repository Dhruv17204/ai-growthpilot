"""
Periodic Data Retention Worker for AI GrowthPilot.

Periodically cleans up expired prompt execution records according to data retention policies
using independent database sessions and resilient async background scheduling.
"""
import asyncio
import logging
from typing import Optional, Callable
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.prompt_service import clean_old_prompt_executions

logger = logging.getLogger("growthpilot.retention")


class PeriodicRetentionWorker:
    """
    Background worker that runs prompt execution retention cleanup at configurable intervals.
    Uses independent database sessions per execution pass to prevent session leaks or contamination.
    """

    def __init__(
        self,
        interval_seconds: int = 86400,
        retention_days: int = 30,
        session_factory: Callable[[], Session] = SessionLocal
    ):
        self.interval_seconds = interval_seconds
        self.retention_days = retention_days
        self.session_factory = session_factory
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False

    def run_cleanup_once(self) -> int:
        """
        Executes a single retention cleanup pass.
        Opens an independent database session, deletes records older than retention_days,
        safely handles exceptions, and always ensures the session is closed.
        """
        db = None
        try:
            db = self.session_factory()
            deleted = clean_old_prompt_executions(db, days=self.retention_days)
            if deleted > 0:
                logger.info(
                    f"Retention worker: Cleaned {deleted} expired prompt execution records "
                    f"(older than {self.retention_days} days)."
                )
            return deleted
        except Exception as exc:
            logger.error(f"Retention worker error during cleanup pass: {exc}", exc_info=True)
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return 0
        finally:
            if db:
                db.close()

    async def _run_loop(self):
        """Internal asynchronous loop that periodically invokes cleanup."""
        self._is_running = True
        logger.info(
            f"Retention worker loop started (interval={self.interval_seconds}s, "
            f"retention={self.retention_days} days)."
        )
        try:
            while self._is_running:
                await asyncio.sleep(self.interval_seconds)
                if not self._is_running:
                    break
                self.run_cleanup_once()
        except asyncio.CancelledError:
            logger.info("Retention worker loop cancelled cleanly.")
            raise
        except Exception as exc:
            logger.error(f"Retention worker unhandled loop exception: {exc}", exc_info=True)
        finally:
            self._is_running = False

    def start(self):
        """Starts the background retention task if not already active."""
        if self._task is None or self._task.done():
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Retention worker background task spawned.")

    async def stop(self):
        """Cleanly cancels and awaits completion of the background retention task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Retention worker background task stopped.")
