"""Add payment/finance unique constraints and sumup_checkout_id

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("sumup_checkout_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_payments_sumup_checkout_id"), "payments", ["sumup_checkout_id"], unique=False)

    op.drop_index(op.f("ix_payments_external_transaction_id"), table_name="payments")
    op.create_index(
        op.f("ix_payments_external_transaction_id"),
        "payments",
        ["external_transaction_id"],
        unique=True,
    )

    op.create_unique_constraint(
        "uq_financial_txn_receipt_category_type",
        "financial_transactions",
        ["receipt_reference", "category", "type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_financial_txn_receipt_category_type", "financial_transactions", type_="unique")

    op.drop_index(op.f("ix_payments_external_transaction_id"), table_name="payments")
    op.create_index(
        op.f("ix_payments_external_transaction_id"),
        "payments",
        ["external_transaction_id"],
        unique=False,
    )

    op.drop_index(op.f("ix_payments_sumup_checkout_id"), table_name="payments")
    op.drop_column("payments", "sumup_checkout_id")
