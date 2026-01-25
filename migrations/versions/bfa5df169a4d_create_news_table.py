"""Create news table

Revision ID: bfa5df169a4d
Revises: 6480eea65bae
Create Date: 2025-12-08 18:30:06.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bfa5df169a4d'
down_revision = '6480eea65bae'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'news',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_published'), 'news', ['published'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_news_published'), table_name='news')
    op.drop_table('news')
