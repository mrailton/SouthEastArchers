"""Create shoots table

Revision ID: c5970e80321a
Revises: cef6e606b3d2
Create Date: 2025-12-08 18:30:03.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c5970e80321a'
down_revision = 'cef6e606b3d2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'shoots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('location', sa.Enum('HALL', 'MEADOW', 'WOODS', name='shootlocation'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shoots_date'), 'shoots', ['date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_shoots_date'), table_name='shoots')
    op.drop_table('shoots')
