"""
Scheduler service for automated news ingestion.
Manages APScheduler lifecycle and scheduled jobs.
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.news_ingestion_service import ingest_latest_gold_news


logger = logging.getLogger(__name__)

# Global scheduler instance (prevents duplicate creation during reloads)
_scheduler: BackgroundScheduler | None = None
# Stores the latest scheduled ingestion result for frontend polling
_latest_scheduled_result: Dict[str, Any] = {}
MALAYSIA_TZ = pytz.timezone("Asia/Kuala_Lumpur")


def _scheduled_news_ingestion():
    """
    Background job function executed by APScheduler.
    Runs daily at 10:00 AM Malaysia time.
    """
    global _latest_scheduled_result
    
    logger.info("🔄 Scheduled news ingestion started")
    
    try:
        result = ingest_latest_gold_news()
        
        processed = result.get("total_processed", 0)
        failed = result.get("total_failed", 0)
        skipped = result.get("total_skipped", 0)
        
        # Store result for frontend polling
        _latest_scheduled_result = {
            "completed_at": datetime.now().isoformat(),
            "total_processed": processed,
            "total_failed": failed,
            "total_skipped": skipped,
            "processed": result.get("processed", []),
            "failed": result.get("failed", []),
            "skipped": result.get("skipped", []),
        }
        
        logger.info(
            "✅ Scheduled news ingestion completed: "
            "%d processed, %d failed, %d skipped",
            processed, failed, skipped
        )
    except Exception as error:
        logger.exception("❌ Scheduled news ingestion failed: %s", str(error))
        _latest_scheduled_result = {
            "completed_at": datetime.now().isoformat(),
            "error": str(error),
            "total_processed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "processed": [],
            "failed": [],
            "skipped": [],
        }


def get_latest_scheduled_result() -> Dict[str, Any]:
    """
    Return the latest scheduled ingestion result.
    Returns empty dict if no scheduled run has completed yet.
    """
    return _latest_scheduled_result.copy() if _latest_scheduled_result else {}


def clear_latest_scheduled_result():
    """Clear the stored result after frontend has seen it."""
    global _latest_scheduled_result
    _latest_scheduled_result = {}


def start_scheduler():
    """
    Start the background scheduler for automated news ingestion.
    Safe to call multiple times (idempotent).
    """
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        logger.info("ℹ️ Scheduler already running")
        return
    
    try:
        _scheduler = BackgroundScheduler(timezone=MALAYSIA_TZ)
        
        # Schedule daily ingestion at 10:00 AM Malaysia time
        _scheduler.add_job(
            _scheduled_news_ingestion,
            trigger=CronTrigger(hour=10, minute=0, timezone=MALAYSIA_TZ),
            id="scheduled_news_ingestion",
            name="Scheduled Gold News Ingestion",
            replace_existing=True,
            misfire_grace_time=600,  # Allow 10 min grace for missed executions
        )
        
        _scheduler.start()
        
        logger.info(
            "🚀 Scheduler started: daily ingestion at 10:00 AM %s",
            MALAYSIA_TZ.zone
        )
        logger.info(
            "Next scheduled ingestion: %s",
            _scheduler.get_job("scheduled_news_ingestion").next_run_time
        )
        
    except Exception as error:
        logger.exception("❌ Failed to start scheduler: %s", str(error))
        _scheduler = None
        raise


def stop_scheduler():
    """
    Stop the background scheduler.
    Safe to call multiple times (idempotent).
    """
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        logger.info("ℹ️ Scheduler not running")
        return
    
    try:
        _scheduler.shutdown(wait=True)
        logger.info("⏹️ Scheduler stopped")
    except Exception as error:
        logger.exception("⚠️ Error stopping scheduler: %s", str(error))
    finally:
        _scheduler = None


def get_scheduler_status() -> dict:
    """
    Get current scheduler status.
    Useful for debugging and monitoring.
    """
    global _scheduler
    
    if _scheduler is None:
        return {
            "running": False,
            "next_run": None,
        }
    
    job = _scheduler.get_job("scheduled_news_ingestion")
    
    return {
        "running": _scheduler.running,
        "next_run": job.next_run_time if job else None,
    }
