import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.report import Report, ReportStatus
from app.services.scheduler_service import run_weekly_report_job, parse_day_of_week

def test_parse_day_of_week():
    assert parse_day_of_week("MONDAY") == "mon"
    assert parse_day_of_week("friday") == "fri"
    assert parse_day_of_week("Sunday") == "sun"
    assert parse_day_of_week("invalid") == "mon"

@pytest.mark.asyncio
async def test_scheduler_idempotency_prevents_duplicate_reports(db: Session):
    # Pre-insert a report generated today
    existing = Report(
        report_period_start=datetime.now(timezone.utc),
        report_period_end=datetime.now(timezone.utc),
        filename="existing_report.pdf",
        file_path="reports/generated/existing_report.pdf",
        status=ReportStatus.SENT.value,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(existing)
    db.commit()

    initial_report_count = len(db.scalars(select(Report)).all())

    # Execute scheduled job routine
    await run_weekly_report_job()

    # Verify no new report was generated due to idempotency check
    final_report_count = len(db.scalars(select(Report)).all())
    assert final_report_count == initial_report_count
