"""Create financial_transactions table

Revision ID: d1e2f3a4b5c6
Revises: b99a8ddc6091
Create Date: 2026-02-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'b99a8ddc6091'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'financial_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('income', 'expense'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('receipt_reference', sa.String(length=255), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_transactions_type'), 'financial_transactions', ['type'], unique=False)
    op.create_index(op.f('ix_financial_transactions_date'), 'financial_transactions', ['date'], unique=False)
    op.create_index(op.f('ix_financial_transactions_created_by_id'), 'financial_transactions', ['created_by_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_financial_transactions_created_by_id'), table_name='financial_transactions')
    op.drop_index(op.f('ix_financial_transactions_date'), table_name='financial_transactions')
    op.drop_index(op.f('ix_financial_transactions_type'), table_name='financial_transactions')
    op.drop_table('financial_transactions')

