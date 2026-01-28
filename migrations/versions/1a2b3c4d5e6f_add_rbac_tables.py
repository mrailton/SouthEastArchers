"""Add RBAC tables and remove is_admin

Revision ID: 1a2b3c4d5e6f
Revises: ac7ad85a658d
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1a2b3c4d5e6f"
down_revision = "ac7ad85a658d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_admin")


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.Boolean(), nullable=True, server_default=sa.text("0")))

    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
