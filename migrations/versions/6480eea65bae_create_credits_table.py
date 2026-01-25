"""Create credits table

Revision ID: 6480eea65bae
Revises: b0e421778d53
Create Date: 2025-12-08 18:30:05.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6480eea65bae'
down_revision = 'b0e421778d53'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'credits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credits_user_id'), 'credits', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_credits_user_id'), table_name='credits')
    op.drop_table('credits')
