from datetime import date

from flask import Response, flash, redirect, request, url_for

from app.services import FinanceService
from app.utils import permission_required
from app.utils.pdf import generate_statement_pdf


class FinancialStatementPdfController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.report")
    def __call__(self):
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if not start_date_str or not end_date_str:
            flash("Please provide start and end dates.", "error")
            return redirect(url_for("admin.financial_statement"))

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("admin.financial_statement"))

        if end_date < start_date:
            flash("End date must be after start date.", "error")
            return redirect(url_for("admin.financial_statement"))

        statement = self.service.generate_statement(start_date=start_date, end_date=end_date)
        pdf_bytes = bytes(generate_statement_pdf(statement))

        filename = f"financial_statement_{start_date_str}_to_{end_date_str}.pdf"
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
