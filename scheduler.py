from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from database import reset_day_stats, reset_week_stats
from config import Config

config = Config()
tz = pytz.timezone(config.TIMEZONE)

scheduler = AsyncIOScheduler(timezone=tz)

scheduler.add_job(reset_day_stats, CronTrigger(hour=0, minute=0, timezone=tz))
scheduler.add_job(reset_week_stats, CronTrigger(day_of_week='mon', hour=0, minute=0, timezone=tz))

def start_scheduler():
    scheduler.start()