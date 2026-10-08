import os
from datetime import datetime, timedelta, timezone
from app.db.models.psf import PSFRecord
from app.services.pdf_service import PDFReportGenerator

def test_pdf_generation_service(tmp_path):
    output_pdf = str(tmp_path / "test_report.pdf")
    
    record_1 = PSFRecord(
        id="rec-1",
        title="Database Migration",
        category="Database",
        status="COMPLETED",
        value={"migrated_tables": 42},
        created_at=datetime.now(timezone.utc)
    )
    record_2 = PSFRecord(
        id="rec-2",
        title="API Rate Limiting",
        category="Security",
        status="ACTIVE",
        value="1000 req/min",
        created_at=datetime.now(timezone.utc)
    )

    start = datetime.now(timezone.utc) - timedelta(days=7)
    end = datetime.now(timezone.utc)

    file_path = PDFReportGenerator.generate_report(
        records=[record_1, record_2],
        period_start=start,
        period_end=end,
        output_filepath=output_pdf
    )

    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 1000  # Non-empty PDF
