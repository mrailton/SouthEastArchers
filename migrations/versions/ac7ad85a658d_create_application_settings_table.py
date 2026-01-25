"""Create application_settings table

Revision ID: ac7ad85a658d
Revises: e77104247124
Create Date: 2026-01-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "ac7ad85a658d"
down_revision = "e77104247124"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "application_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("membership_year_start_month", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("membership_year_start_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("annual_membership_cost", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("membership_shoots_included", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("additional_shoot_cost", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create the default settings record
    op.execute(
        """
        INSERT INTO application_settings (
            membership_year_start_month,
            membership_year_start_day,
            annual_membership_cost,
            membership_shoots_included,
            additional_shoot_cost,
            created_at,
            updated_at
        ) VALUES (
            3,
            1,
            10000,
            20,
            500,
            '',
            '',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """
    )


def downgrade():
    op.drop_table("application_settings")
