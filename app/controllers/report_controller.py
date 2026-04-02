import logging
import asyncio
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.controllers.base_controller import BaseController
from app.core.config import Settings
from app.models.contract import Contract
from app.models.risk_score import RiskScore
from app.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)


class ReportController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)

    async def generate(self, contract_uuid: str) -> Optional[str]:
        stmt_contract = select(Contract).where(Contract.uuid == contract_uuid)
        result_contract = await self.db.execute(stmt_contract)
        contract = result_contract.scalars().first()

        if not contract:
            return None

        stmt_risk = select(RiskScore).where(RiskScore.contract_id == contract.id)
        result_risk = await self.db.execute(stmt_risk)
        risk_score = result_risk.scalars().first()

        stmt_chat = select(ChatHistory).where(ChatHistory.contract_id == contract.id)
        result_chat = await self.db.execute(stmt_chat)
        chat_history = result_chat.scalars().all()

        file_path = f"uploads/report_{contract_uuid}.pdf"

        def build_pdf():
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=24,
                textColor=HexColor('#1a1a2e'),
                spaceAfter=20
            )

            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=HexColor('#16213e'),
                spaceAfter=10,
                spaceBefore=20
            )

            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                leading=16
            )

            story.append(Paragraph(f"Contract Analysis Report", title_style))
            story.append(Paragraph(f"{contract.name}", heading_style))
            story.append(Spacer(1, 0.5 * cm))

            story.append(Paragraph("Contract Information", heading_style))
            info_data = [
                ["Contract Name", contract.name],
                ["Contract Type", contract.contract_type.value if contract.contract_type else "N/A"],
                ["Status", contract.status.value if contract.status else "N/A"],
                ["Upload Date", contract.created_at.strftime("%B %d, %Y")],
            ]
            info_table = Table(info_data, colWidths=[5 * cm, 12 * cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f0')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(info_table)

            if contract.summary:
                story.append(Paragraph("Summary", heading_style))
                story.append(Paragraph(contract.summary, body_style))

            if risk_score:
                story.append(Paragraph("Risk Assessment", heading_style))
                story.append(Paragraph(f"Overall Risk Score: {risk_score.overall_score}/10", body_style))

                risk_data = [["Category", "Score"]]
                if risk_score.termination_score:
                    risk_data.append(["Termination", f"{risk_score.termination_score}/10"])
                if risk_score.non_compete_score:
                    risk_data.append(["Non-Compete", f"{risk_score.non_compete_score}/10"])
                if risk_score.ip_clauses_score:
                    risk_data.append(["IP Ownership", f"{risk_score.ip_clauses_score}/10"])
                if risk_score.payment_score:
                    risk_data.append(["Payment", f"{risk_score.payment_score}/10"])
                if risk_score.auto_renewal_score:
                    risk_data.append(["Auto-Renewal", f"{risk_score.auto_renewal_score}/10"])

                risk_table = Table(risk_data, colWidths=[10 * cm, 7 * cm])
                risk_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#16213e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9f9f9')]),
                ]))
                story.append(risk_table)

                if risk_score.red_flags:
                    story.append(Paragraph("Red Flags", heading_style))
                    story.append(Paragraph(risk_score.red_flags, body_style))

            if chat_history:
                story.append(Paragraph("Q&A History", heading_style))
                for chat in chat_history:
                    story.append(Paragraph(f"Q: {chat.question}", body_style))
                    story.append(Paragraph(f"A: {chat.answer}", body_style))
                    if chat.risk_score:
                        story.append(Paragraph(f"Risk Score: {chat.risk_score}/10", body_style))
                    story.append(Spacer(1, 0.3 * cm))

            doc.build(story)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, build_pdf)

        logger.info(f"Report generated: {file_path}")
        return file_path