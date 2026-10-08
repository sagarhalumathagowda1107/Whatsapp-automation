import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.db.models.report import Report, ReportStatus
from app.db.models.recipient import Recipient
from app.db.models.message_log import WhatsAppMessageLog, MessageLogStatus
from app.services.psf_service import PSFService
from app.services.pdf_service import PDFReportGenerator
from app.services.whatsapp_service import whatsapp_service, WhatsAppServiceError
from app.utils.logger import logger

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ReportService:

    @staticmethod
    def generate_report(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Report:
        if not end_date:
            end_date = utc_now()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        # 1. Fetch PSF records for the period
        records = PSFService.list_psf(
            db,
            skip=0,
            limit=1000,
            start_date=start_date,
            end_date=end_date
        )

        # 2. Prepare storage path & filename
        filename = f"weekly_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}.pdf"
        file_path = os.path.join(settings.REPORT_STORAGE_PATH, filename)

        # 3. Generate PDF file using ReportLab
        PDFReportGenerator.generate_report(
            records=records,
            period_start=start_date,
            period_end=end_date,
            output_filepath=file_path
        )

        # 4. Save Report record in database
        report = Report(
            report_period_start=start_date,
            report_period_end=end_date,
            filename=filename,
            file_path=file_path,
            status=ReportStatus.GENERATED.value,
            generated_at=utc_now()
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        logger.info(f"Generated PDF report {report.id} ({filename}) for period {start_date} to {end_date}")
        return report

    @staticmethod
    async def send_report_to_recipients(db: Session, report_id: str) -> Report:
        report = db.scalar(
            select(Report).where(Report.id == report_id).options(joinedload(Report.message_logs))
        )
        if not report:
            raise ValueError(f"Report with ID {report_id} not found")

        # Get active recipients
        active_recipients = db.scalars(
            select(Recipient).where(Recipient.active == True)
        ).all()

        if not active_recipients:
            logger.warning(f"No active recipients found to send report {report_id}")
            report.status = ReportStatus.SENT.value
            report.sent_at = utc_now()
            db.commit()
            db.refresh(report)
            return report

        report.status = ReportStatus.SENDING.value
        db.commit()

        # 1. Upload media to WhatsApp API once
        try:
            media_id = await whatsapp_service.upload_media(report.file_path, mime_type="application/pdf")
        except Exception as e:
            logger.error(f"Failed to upload report PDF to WhatsApp: {str(e)}")
            report.status = ReportStatus.FAILED.value
            db.commit()
            raise WhatsAppServiceError(f"Media upload failed: {str(e)}")

        caption = f"📄 Weekly Performance & PSF Report ({report.report_period_start.strftime('%d %b')} - {report.report_period_end.strftime('%d %b %Y')})"
        
        success_count = 0
        failure_count = 0

        # 2. Send document to each recipient
        for recipient in active_recipients:
            # Create or reuse message log
            log = WhatsAppMessageLog(
                report_id=report.id,
                recipient_id=recipient.id,
                status=MessageLogStatus.PENDING.value,
                request_timestamp=utc_now()
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            try:
                resp = await whatsapp_service.send_document_message(
                    to_phone=recipient.phone_number,
                    media_id=media_id,
                    filename=report.filename,
                    caption=caption
                )
                
                messages = resp.get("messages", [])
                wamid = messages[0].get("id") if messages else None
                
                log.whatsapp_message_id = wamid
                log.status = MessageLogStatus.SENT.value
                log.sent_at = utc_now()
                success_count += 1
                logger.info(f"Successfully dispatched report {report.id} to recipient {recipient.phone_number} (WAMID: {wamid})")
                
            except WhatsAppServiceError as err:
                failure_count += 1
                log.status = MessageLogStatus.FAILED.value
                log.error_code = str(err.status_code) if err.status_code else "API_ERROR"
                log.error_message = str(err)
                logger.error(f"Failed to send report {report.id} to {recipient.phone_number}: {err}")
            except Exception as ex:
                failure_count += 1
                log.status = MessageLogStatus.FAILED.value
                log.error_code = "UNKNOWN_ERROR"
                log.error_message = str(ex)
                logger.error(f"Unexpected error sending report to {recipient.phone_number}: {ex}")

            db.commit()

        # Update final report status
        if success_count > 0 and failure_count == 0:
            report.status = ReportStatus.SENT.value
        elif success_count > 0 and failure_count > 0:
            report.status = ReportStatus.PARTIALLY_SENT.value
        else:
            report.status = ReportStatus.FAILED.value

        report.sent_at = utc_now()
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    async def retry_failed_deliveries(db: Session, report_id: str) -> Report:
        report = db.scalar(
            select(Report).where(Report.id == report_id).options(joinedload(Report.message_logs))
        )
        if not report:
            raise ValueError(f"Report with ID {report_id} not found")

        failed_logs = [log for log in report.message_logs if log.status == MessageLogStatus.FAILED.value]
        if not failed_logs:
            logger.info(f"No failed delivery logs found for report {report_id}")
            return report

        # Upload media once
        media_id = await whatsapp_service.upload_media(report.file_path, mime_type="application/pdf")
        caption = f"📄 [RETRY] Weekly Performance Report ({report.report_period_start.strftime('%d %b')} - {report.report_period_end.strftime('%d %b %Y')})"

        for log in failed_logs:
            recipient = db.scalar(select(Recipient).where(Recipient.id == log.recipient_id))
            if not recipient or not recipient.active:
                continue

            try:
                resp = await whatsapp_service.send_document_message(
                    to_phone=recipient.phone_number,
                    media_id=media_id,
                    filename=report.filename,
                    caption=caption
                )
                messages = resp.get("messages", [])
                wamid = messages[0].get("id") if messages else None
                
                log.whatsapp_message_id = wamid
                log.status = MessageLogStatus.SENT.value
                log.sent_at = utc_now()
                log.error_code = None
                log.error_message = None
            except Exception as err:
                log.error_message = f"Retry failed: {str(err)}"

            db.commit()

        # Update overall status
        remaining_failures = any(l.status == MessageLogStatus.FAILED.value for l in report.message_logs)
        if not remaining_failures:
            report.status = ReportStatus.SENT.value
        else:
            report.status = ReportStatus.PARTIALLY_SENT.value

        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_report(db: Session, report_id: str) -> Optional[Report]:
        return db.scalar(
            select(Report).where(Report.id == report_id).options(joinedload(Report.message_logs))
        )

    @staticmethod
    def list_reports(db: Session, skip: int = 0, limit: int = 100) -> List[Report]:
        stmt = select(Report).order_by(Report.generated_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
