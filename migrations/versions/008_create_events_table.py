"""Create events table

Revision ID: 008
Revises: 007
Create Date: 2025-12-08 18:30:07.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_published'), 'events', ['published'], unique=False)
    op.create_index(op.f('ix_events_start_date'), 'events', ['start_date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_events_start_date'), table_name='events')
    op.drop_index(op.f('ix_events_published'), table_name='events')
    op.drop_table('events')
