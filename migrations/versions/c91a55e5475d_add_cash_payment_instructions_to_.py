"""Add cash_payment_instructions to application_settings

Revision ID: c91a55e5475d
Revises: 1a2b3c4d5e6f
Create Date: 2026-02-17 23:42:49.882429

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c91a55e5475d'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

DEFAULT_INSTRUCTIONS = "Please pay cash to a committee member at the next shoot night. Your membership/credits will be activated once payment is confirmed."


def upgrade():
    # MySQL doesn't allow default values on TEXT columns, so we:
    # 1. Add column as nullable
    # 2. Update existing rows with default value
    # 3. Make column NOT NULL
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cash_payment_instructions', sa.Text(), nullable=True))

    # Set default value for any existing rows
    op.execute(f"UPDATE application_settings SET cash_payment_instructions = '{DEFAULT_INSTRUCTIONS}' WHERE cash_payment_instructions IS NULL")

    # Make column NOT NULL
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.alter_column('cash_payment_instructions', existing_type=sa.Text(), nullable=False)


def downgrade():
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.drop_column('cash_payment_instructions')
