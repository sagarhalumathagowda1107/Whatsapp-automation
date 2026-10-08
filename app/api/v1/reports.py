from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import verify_admin_api_key
from app.schemas.report import (
    ReportGenerateRequest, ReportResponse, ReportDetailResponse
)
from app.services.report_service import ReportService
from app.services.whatsapp_service import WhatsAppServiceError

router = APIRouter(prefix="/reports", tags=["Report Management & Dispatch"])

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Generate Weekly PDF Report")
async def generate_report(
    payload: Optional[ReportGenerateRequest] = None,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """
    Manually generate a weekly PDF report for a specified reporting period.
    If send_immediately is true, the report will be dispatched to all active recipients immediately.
    """
    start_date = payload.start_date if payload else None
    end_date = payload.end_date if payload else None
    send_immediately = payload.send_immediately if payload else False

    report = ReportService.generate_report(db, start_date=start_date, end_date=end_date)

    if send_immediately:
        try:
            report = await ReportService.send_report_to_recipients(db, report.id)
        except WhatsAppServiceError as err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Report generated but WhatsApp delivery failed: {str(err)}"
            )

    return report

@router.get("", response_model=List[ReportResponse], summary="List Generated Reports")
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """List generated PDF reports."""
    return ReportService.list_reports(db, skip=skip, limit=limit)

@router.get("/{id}", response_model=ReportDetailResponse, summary="Get Report Details & Delivery Logs")
def get_report(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Retrieve detailed report metadata and individual recipient message logs."""
    report = ReportService.get_report(db, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{id}' not found")
    return report

@router.post("/{id}/send", response_model=ReportDetailResponse, summary="Send Existing Report via WhatsApp")
async def send_report(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Dispatch an existing PDF report to active WhatsApp recipients."""
    try:
        report = await ReportService.send_report_to_recipients(db, id)
        return report
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except WhatsAppServiceError as err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))

@router.post("/{id}/retry", response_model=ReportDetailResponse, summary="Retry Failed WhatsApp Deliveries")
async def retry_failed_report_send(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    """Retry sending the PDF report to recipients whose previous delivery status was FAILED."""
    try:
        report = await ReportService.retry_failed_deliveries(db, id)
        return report
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except WhatsAppServiceError as err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))
