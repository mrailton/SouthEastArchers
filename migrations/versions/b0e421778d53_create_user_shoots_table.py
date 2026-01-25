"""Create user_shoots association table

Revision ID: b0e421778d53
Revises: c5970e80321a
Create Date: 2025-12-08 18:30:04.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b0e421778d53'
down_revision = 'c5970e80321a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_shoots',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shoot_id', sa.Integer(), nullable=False),
        sa.Column('attended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shoot_id'], ['shoots.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'shoot_id')
    )


def downgrade():
    op.drop_table('user_shoots')
