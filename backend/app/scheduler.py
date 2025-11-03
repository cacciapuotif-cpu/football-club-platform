"""
Background job scheduler using APScheduler.

Schedules automatic execution of:
- calc_metrics: Daily at 03:00 (calculates ACWR, Monotony, Strain, Readiness)
- generate_alerts: Daily at 04:00 (generates player alerts based on metrics)
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.calc_metrics import update_player_metrics
from app.jobs.generate_alerts import generate_alerts

logger = logging.getLogger(__name__)


def setup_scheduler() -> AsyncIOScheduler:
    """
    Setup and configure the background job scheduler.

    Returns:
        AsyncIOScheduler instance (not started yet)
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")

    # Schedule metrics calculation daily at 03:00
    scheduler.add_job(
        update_player_metrics,
        trigger=CronTrigger(hour=3, minute=0),
        id="calc_metrics_daily",
        name="Calculate daily metrics (ACWR, Monotony, Strain, Readiness)",
        replace_existing=True,
        misfire_grace_time=3600,  # Allow 1 hour grace period
    )
    logger.info("✅ Scheduled update_player_metrics job to run daily at 03:00")

    # Schedule alert generation daily at 04:00
    scheduler.add_job(
        generate_alerts,
        trigger=CronTrigger(hour=4, minute=0),
        id="generate_alerts_daily",
        name="Generate player alerts based on metrics",
        replace_existing=True,
        misfire_grace_time=3600,  # Allow 1 hour grace period
    )
    logger.info("✅ Scheduled generate_alerts job to run daily at 04:00")

    return scheduler


def start_scheduler(scheduler: AsyncIOScheduler):
    """
    Start the scheduler.

    Args:
        scheduler: AsyncIOScheduler instance
    """
    try:
        scheduler.start()
        logger.info("🔄 Background job scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def shutdown_scheduler(scheduler: AsyncIOScheduler):
    """
    Gracefully shutdown the scheduler.

    Args:
        scheduler: AsyncIOScheduler instance
    """
    try:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Background job scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)
