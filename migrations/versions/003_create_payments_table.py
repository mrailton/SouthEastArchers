"""Create payments table

Revision ID: 003
Revises: 002
Create Date: 2025-12-08 18:30:02.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('payment_type', sa.Enum('membership', 'credits', name='payment_type'), nullable=False),
        sa.Column('payment_method', sa.Enum('cash', 'online', name='payment_method'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'cancelled', name='payment_status'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('payment_processor', sa.String(length=50), nullable=True),
        sa.Column('external_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_external_transaction_id'), 'payments', ['external_transaction_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_payments_external_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_table('payments')
