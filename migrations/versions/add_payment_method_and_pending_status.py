"""Add payment_method to payments and support pending membership status

Revision ID: add_payment_method
Revises: 316fc5a90bd1
Create Date: 2025-11-20 18:12:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_payment_method"
down_revision = "316fc5a90bd1"
branch_labels = None
depends_on = None


def upgrade():
    # Add payment_method column to payments table
    op.add_column(
        "payments",
        sa.Column(
            "payment_method",
            sa.Enum("cash", "online", name="payment_method_enum"),
            nullable=False,
            server_default="online",
        ),
    )

    # Update membership status default to 'pending' is handled by the model
    # Existing memberships remain 'active' unless explicitly changed


def downgrade():
    # Remove payment_method column
    op.drop_column("payments", "payment_method")

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS payment_method_enum")
