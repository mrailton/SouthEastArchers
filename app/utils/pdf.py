from __future__ import annotations

from datetime import date


def generate_statement_pdf(statement: dict) -> bytes:
    """Render a financial *statement* dict as a PDF and return the raw bytes.

    The *statement* is the dict produced by
    ``FinanceService.generate_statement()`` and must contain at least:

    - ``start_date``, ``end_date``
    - ``total_income``, ``total_expenses``, ``net``
    - ``income_by_category``, ``expense_by_category``
    - ``income_items``, ``expense_items``
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    eur = "EUR "

    # --- Title ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "South East Archers", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Financial Statement", new_x="LMARGIN", new_y="NEXT", align="C")

    # --- Period ---
    pdf.set_font("Helvetica", "", 10)
    period = f"{statement['start_date'].strftime('%d %B %Y')} - {statement['end_date'].strftime('%d %B %Y')}"
    pdf.cell(0, 8, period, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # --- Summary box ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(63, 8, f"Total Income:  {eur}{statement['total_income']:.2f}", border=1, fill=True)
    pdf.cell(63, 8, f"Total Expenses:  {eur}{statement['total_expenses']:.2f}", border=1, fill=True)
    net = statement["net"]
    net_label = f"Net Balance:  {eur}{abs(net):.2f}" if net >= 0 else f"Net Balance:  -{eur}{abs(net):.2f}"
    pdf.cell(64, 8, net_label, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # --- Category breakdowns ---
    _render_category_breakdown(pdf, "Income", statement.get("income_by_category", []), (0, 128, 0), eur)
    _render_category_breakdown(pdf, "Expenses", statement.get("expense_by_category", []), (192, 0, 0), eur)

    # --- Transaction tables ---
    _render_transaction_table(pdf, "Income", statement["income_items"], (0, 128, 0), eur)
    _render_transaction_table(pdf, "Expenses", statement["expense_items"], (192, 0, 0), eur)

    # --- Footer ---
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    generated = date.today().strftime("%d %B %Y")
    pdf.cell(0, 6, f"Generated on {generated} | South East Archers", align="C")

    return bytes(pdf.output() or b"")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CAT_LABEL_W = 120
_CAT_COUNT_W = 30
_CAT_AMT_W = 40

_COL_DATE_W = 28
_COL_CAT_W = 40
_COL_DESC_W = 82
_COL_AMT_W = 40


def _render_category_breakdown(pdf, title: str, categories: list, color: tuple, eur: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*color)
    pdf.cell(0, 9, f"{title} by Category", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if not categories:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, f"No {title.lower()} for this period.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    # Header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(_CAT_LABEL_W, 7, "Category", border=1, fill=True)
    pdf.cell(_CAT_COUNT_W, 7, "Count", border=1, fill=True, align="C")
    pdf.cell(_CAT_AMT_W, 7, "Amount", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # Rows
    pdf.set_font("Helvetica", "", 9)
    for cat in categories:
        pdf.cell(_CAT_LABEL_W, 7, cat["label"], border=1)
        pdf.cell(_CAT_COUNT_W, 7, str(cat["count"]), border=1, align="C")
        pdf.cell(_CAT_AMT_W, 7, f"{eur}{cat['total']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)


def _render_transaction_table(pdf, title: str, items: list, color: tuple, eur: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*color)
    pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if not items:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, f"No {title.lower()} recorded for this period.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(_COL_DATE_W, 7, "Date", border=1, fill=True)
    pdf.cell(_COL_CAT_W, 7, "Category", border=1, fill=True)
    pdf.cell(_COL_DESC_W, 7, "Description", border=1, fill=True)
    pdf.cell(_COL_AMT_W, 7, "Amount", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    total_cents = 0
    for item in items:
        total_cents += item.amount_cents
        category_label = item.category.replace("_", " ").title()
        desc = item.description[:45] + "..." if len(item.description) > 48 else item.description
        pdf.cell(_COL_DATE_W, 7, item.date.strftime("%Y-%m-%d"), border=1)
        pdf.cell(_COL_CAT_W, 7, category_label, border=1)
        pdf.cell(_COL_DESC_W, 7, desc, border=1)
        pdf.cell(_COL_AMT_W, 7, f"{eur}{item.amount:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    # Total row
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(_COL_DATE_W + _COL_CAT_W + _COL_DESC_W, 7, "Total", border=1)
    pdf.cell(_COL_AMT_W, 7, f"{eur}{total_cents / 100:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
