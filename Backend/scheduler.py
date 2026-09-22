import asyncio
import logging
from datetime import datetime, timezone, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import async_session
from job_parser import parse_all_sources

logger = logging.getLogger("scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Dushanbe")


async def run_daily_parse():
    logger.info(f"[{datetime.now(timezone.utc).isoformat()}] Starting daily job parse...")
    try:
        result = await parse_all_sources(max_jobs_per_source=30)
        logger.info(f"Daily parse completed: {result}")
    except Exception as e:
        logger.error(f"Daily parse failed: {e}")


def setup_scheduler():
    scheduler.add_job(
        run_daily_parse,
        CronTrigger(hour=17, minute=0),
        id="daily_job_parse",
        name="Daily Job Parsing at 5PM",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started - daily parse at 17:00 Asia/Dushanbe")
