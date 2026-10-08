from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from app.config import settings
from app.db.session import SessionLocal
from app.db.models.report import Report, ReportStatus
from app.services.report_service import ReportService
from app.utils.logger import logger

scheduler = AsyncIOScheduler()

def parse_day_of_week(day_str: str) -> str:
    """Normalize day of week string e.g. MONDAY -> mon"""
    d = day_str.strip().lower()
    mapping = {
        "monday": "mon", "mon": "mon", "0": "mon",
        "tuesday": "tue", "tue": "tue", "1": "tue",
        "wednesday": "wed", "wed": "wed", "2": "wed",
        "thursday": "thu", "thu": "thu", "3": "thu",
        "friday": "fri", "fri": "fri", "4": "fri",
        "saturday": "sat", "sat": "sat", "5": "sat",
        "sunday": "sun", "sun": "sun", "6": "sun",
    }
    return mapping.get(d, "mon")

async def run_weekly_report_job():
    """
    Weekly automated task.
    Includes an idempotency guard so application restarts do not duplicate weekly reports.
    """
    logger.info("Executing scheduled weekly report job...")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=7)
        period_end = now

        # Idempotency check: Look for any report generated within the last 6 days
        six_days_ago = now - timedelta(days=6)
        existing_report = db.scalar(
            select(Report).where(
                Report.generated_at >= six_days_ago,
                Report.status.in_([
                    ReportStatus.GENERATED.value,
                    ReportStatus.SENDING.value,
                    ReportStatus.SENT.value,
                    ReportStatus.PARTIALLY_SENT.value
                ])
            )
        )

        if existing_report:
            logger.info(f"Skipping scheduled weekly report: Report {existing_report.id} was already generated on {existing_report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
            return

        # Generate & Send
        report = ReportService.generate_report(db, start_date=period_start, end_date=period_end)
        await ReportService.send_report_to_recipients(db, report.id)
        logger.info(f"Scheduled weekly report workflow completed successfully for report {report.id}")

    except Exception as err:
        logger.error(f"Error in weekly report scheduled job: {err}", exc_info=True)
    finally:
        db.close()

def start_scheduler():
    """Starts the APScheduler background task."""
    if scheduler.running:
        return

    day_of_week = parse_day_of_week(settings.REPORT_DAY)
    try:
        hour, minute = map(int, settings.REPORT_TIME.split(":"))
    except ValueError:
        hour, minute = 9, 0

    trigger = CronTrigger(
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        timezone=settings.REPORT_TIMEZONE
    )

    scheduler.add_job(
        run_weekly_report_job,
        trigger=trigger,
        id="weekly_whatsapp_report_job",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"APScheduler started. Scheduled weekly report for day '{settings.REPORT_DAY}' ({day_of_week}) at {settings.REPORT_TIME} {settings.REPORT_TIMEZONE}")

def stop_scheduler():
    """Stops the APScheduler background task."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped successfully.")
