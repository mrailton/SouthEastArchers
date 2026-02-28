"""Add visitor_shoot_fee and shoot_visitors table

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "a3b4c5d6e7f8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    # Add visitor shoot fee to settings
    op.add_column("application_settings", sa.Column("visitor_shoot_fee", sa.Integer(), nullable=False, server_default="1000"))

    # Create shoot_visitors table
    op.create_table(
        "shoot_visitors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shoot_id", sa.Integer(), sa.ForeignKey("shoots.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("club", sa.String(255), nullable=False),
        sa.Column("affiliation", sa.String(10), nullable=False),
        sa.Column("payment_method", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("shoot_visitors")
    op.drop_column("application_settings", "visitor_shoot_fee")
