import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Transaction, TransactionStatus
from app.utils.dates import end_datetime, start_datetime


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def _filters(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        payment_method: str | None,
        status: str | None,
    ) -> list[Any]:
        filters = []
        if start_date:
            parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            filters.append(Transaction.created_at >= start_datetime(parsed))
        if end_date:
            parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            filters.append(Transaction.created_at <= end_datetime(parsed))
        if payment_method:
            filters.append(Transaction.payment_method == payment_method.upper())
        if status:
            filters.append(Transaction.status == status.upper())
        return filters

    def transactions(self, *, cashier_id: int | None = None,
                     start_date: str | None = None,
                     end_date: str | None = None,
                     payment_method: str | None = None,
                     status: str | None = None) -> list[Transaction]:
        filters = self._filters(
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            status=status,
        )
        if cashier_id is not None:
            filters.append(Transaction.cashier_id == cashier_id)
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.cashier))
            .where(*filters)
            .order_by(Transaction.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def _to_rows(transactions: list[Transaction]) -> list[list[str]]:
        rows = []
        for t in transactions:
            rows.append([
                t.invoice_number,
                t.cashier.username if t.cashier else "",
                t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
                t.payment_method,
                t.status,
                f"{t.subtotal:.2f}",
                f"{t.discount:.2f}",
                f"{t.total:.2f}",
                f"{t.paid_amount:.2f}",
                f"{t.change_amount:.2f}",
            ])
        return rows

    def transactions_csv(self, *, cashier_id: int | None = None,
                         start_date: str | None = None,
                         end_date: str | None = None,
                         payment_method: str | None = None,
                         status: str | None = None) -> str:
        transactions = self.transactions(
            cashier_id=cashier_id,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            status=status,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "invoice_number", "cashier", "created_at", "payment_method", "status",
            "subtotal", "discount", "total", "paid_amount", "change_amount",
        ])
        writer.writerows(self._to_rows(transactions))
        return buffer.getvalue()

    def transactions_pdf(self, *, cashier_id: int | None = None,
                         start_date: str | None = None,
                         end_date: str | None = None,
                         payment_method: str | None = None,
                         status: str | None = None) -> bytes:
        transactions = self.transactions(
            cashier_id=cashier_id,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            status=status,
        )
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        styles = getSampleStyleSheet()
        title = Paragraph("Laporan Transaksi", styles["Title"])

        data = [[
            "Invoice", "Kasir", "Waktu", "Pembayaran", "Status",
            "Subtotal", "Diskon", "Total", "Dibayar", "Kembalian",
        ]]
        for row in self._to_rows(transactions):
            data.append([Paragraph(c, styles["BodyText"]) for c in row])

        table = Table(data, repeatRows=1, colWidths=[42 * mm, 30 * mm, 40 * mm, 25 * mm, 22 * mm,
                                                     25 * mm, 22 * mm, 25 * mm, 25 * mm, 25 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3B52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6FA")]),
        ]))

        if transactions:
            total_sales = sum((t.total or Decimal("0")) for t in transactions
                              if t.status != TransactionStatus.CANCELLED.value)
            summary = Paragraph(
                f"Total transaksi: {len(transactions)} | Total penjualan (non-batal): "
                f"Rp{float(total_sales):,.2f}".replace(",", "."),
                styles["Normal"],
            )
        else:
            summary = Paragraph("Tidak ada data.", styles["Normal"])

        story = [title, Spacer(1, 4), summary, Spacer(1, 6), table]
        doc.build(story)
        return buffer.getvalue()