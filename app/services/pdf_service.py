import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from app.config import settings
from app.db.models.psf import PSFRecord

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header and footer on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Draw header bar for page > 1
        if self._pageNumber > 1:
            self.drawString(36, 756, f"{settings.COMPANY_NAME} | Weekly Performance & PSF Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(36, 748, 576, 748)
            
        # Draw footer for all pages
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_text)
        self.drawString(36, 30, "CONFIDENTIAL — FOR INTERNAL USE ONLY")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(36, 42, 576, 42)
        
        self.restoreState()

class PDFReportGenerator:
    """Service to generate clean, professional PDF reports from PSF records."""

    @staticmethod
    def generate_report(
        records: List[PSFRecord],
        period_start: datetime,
        period_end: datetime,
        output_filepath: str
    ) -> str:
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # Custom typography styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#475569"),
            spaceAfter=15
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=12,
            spaceAfter=8
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        
        bold_body = ParagraphStyle(
            'BoldBody',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        table_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )
        
        table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=table_cell,
            fontName='Helvetica-Bold'
        )

        elements = []
        
        # Document Header Section
        elements.append(Paragraph(f"{settings.COMPANY_NAME}", title_style))
        elements.append(Paragraph("Weekly Executive Performance & PSF Report", ParagraphStyle('SubTitle2', parent=title_style, fontSize=16, leading=20, textColor=colors.HexColor("#2563EB"))))
        
        period_str = f"{period_start.strftime('%d %b %Y')} to {period_end.strftime('%d %b %Y')}"
        gen_str = datetime.now().strftime('%d %b %Y %H:%M UTC')
        elements.append(Paragraph(f"<b>Reporting Period:</b> {period_str} | <b>Generated:</b> {gen_str}", subtitle_style))
        
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=15))
        
        # 1. Executive Summary Section
        total_count = len(records)
        status_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        
        for r in records:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            category_counts[r.category] = category_counts.get(r.category, 0) + 1

        summary_text = (
            f"During the reporting period, a total of <b>{total_count} PSF records</b> were evaluated across "
            f"<b>{len(category_counts)} categories</b>. The current distribution includes "
            + ", ".join([f"<b>{cnt} {st}</b>" for st, cnt in status_counts.items()])
            + "." if total_count > 0 else "No PSF records were logged for this reporting period."
        )
        
        elements.append(Paragraph("Executive Summary", section_style))
        
        # Summary KPI Box Table
        kpi_data = [
            [
                Paragraph("<b>Total Items</b>", table_cell_bold),
                Paragraph("<b>Active</b>", table_cell_bold),
                Paragraph("<b>Completed</b>", table_cell_bold),
                Paragraph("<b>Categories</b>", table_cell_bold)
            ],
            [
                Paragraph(str(total_count), title_style),
                Paragraph(str(status_counts.get("ACTIVE", 0)), title_style),
                Paragraph(str(status_counts.get("COMPLETED", 0)), title_style),
                Paragraph(str(len(category_counts)), title_style)
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 15))
        
        # 2. Category Summary Table
        if category_counts:
            elements.append(Paragraph("Category Breakdown", section_style))
            cat_table_data = [[
                Paragraph("<b>Category</b>", table_cell_bold),
                Paragraph("<b>Count</b>", table_cell_bold),
                Paragraph("<b>Share (%)</b>", table_cell_bold)
            ]]
            for cat, count in category_counts.items():
                pct = (count / total_count * 100) if total_count > 0 else 0
                cat_table_data.append([
                    Paragraph(cat, table_cell),
                    Paragraph(str(count), table_cell),
                    Paragraph(f"{pct:.1f}%", table_cell)
                ])
                
            cat_table = Table(cat_table_data, colWidths=[240, 150, 150])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(cat_table)
            elements.append(Spacer(1, 15))
        
        # 3. Detailed PSF Table
        elements.append(Paragraph("Detailed PSF Data Log", section_style))
        
        psf_headers = [
            Paragraph("<b>Title</b>", table_cell_bold),
            Paragraph("<b>Category</b>", table_cell_bold),
            Paragraph("<b>Status</b>", table_cell_bold),
            Paragraph("<b>Value / Info</b>", table_cell_bold),
            Paragraph("<b>Date</b>", table_cell_bold)
        ]
        
        psf_table_data = [psf_headers]
        
        for r in records:
            val_str = str(r.value) if r.value is not None else "-"
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
                
            psf_table_data.append([
                Paragraph(r.title, table_cell_bold),
                Paragraph(r.category, table_cell),
                Paragraph(r.status, table_cell),
                Paragraph(val_str, table_cell),
                Paragraph(r.created_at.strftime('%Y-%m-%d'), table_cell)
            ])
            
        if len(psf_table_data) == 1:
            psf_table_data.append([
                Paragraph("No records found", table_cell),
                Paragraph("-", table_cell),
                Paragraph("-", table_cell),
                Paragraph("-", table_cell),
                Paragraph("-", table_cell)
            ])

        psf_table = Table(psf_table_data, colWidths=[140, 90, 80, 140, 90])
        psf_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        
        elements.append(psf_table)
        
        doc.build(elements, canvasmaker=NumberedCanvas)
        return output_filepath
