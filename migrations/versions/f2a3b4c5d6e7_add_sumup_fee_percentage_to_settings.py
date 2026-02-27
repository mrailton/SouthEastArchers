"""Add sumup_fee_percentage to application_settings

Revision ID: f2a3b4c5d6e7
Revises: d1e2f3a4b5c6
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "f2a3b4c5d6e7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "application_settings",
        sa.Column("sumup_fee_percentage", sa.Numeric(5, 2), nullable=True),
    )


def downgrade():
    op.drop_column("application_settings", "sumup_fee_percentage")
