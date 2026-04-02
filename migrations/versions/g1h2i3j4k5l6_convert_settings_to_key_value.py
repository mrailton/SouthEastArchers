"""Convert application_settings singleton to key-value setting table

Revision ID: g1h2i3j4k5l6
Revises: a3b4c5d6e7f8
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "g1h2i3j4k5l6"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None

# Columns to migrate and how to serialise them.
# Boolean columns are converted to "true"/"false"; everything else uses str().
_BOOL_COLUMNS = {"news_enabled", "events_enabled"}
_COLUMNS = [
    "membership_year_start_month",
    "membership_year_start_day",
    "annual_membership_cost",
    "membership_shoots_included",
    "additional_shoot_cost",
    "visitor_shoot_fee",
    "news_enabled",
    "events_enabled",
    "cash_payment_instructions",
    "sumup_fee_percentage",
]


def upgrade():
    # 1. Create the new key-value table
    op.create_table(
        "setting",
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    # 2. Copy data from the singleton row (if it exists) into key-value rows
    conn = op.get_bind()
    row = conn.execute(sa.text("SELECT * FROM application_settings LIMIT 1")).mappings().first()

    if row:
        for col in _COLUMNS:
            raw = row.get(col)
            if raw is None:
                value = None
            elif col in _BOOL_COLUMNS:
                value = "true" if raw else "false"
            else:
                value = str(raw)

            conn.execute(
                sa.text("INSERT INTO setting (`key`, value, updated_at) VALUES (:k, :v, CURRENT_TIMESTAMP)"),
                {"k": col, "v": value},
            )

    # 3. Drop the old table
    op.drop_table("application_settings")


def downgrade():
    # Recreate the old singleton table
    op.create_table(
        "application_settings",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("membership_year_start_month", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("membership_year_start_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("annual_membership_cost", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("membership_shoots_included", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("additional_shoot_cost", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("news_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("events_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("cash_payment_instructions", sa.Text(), nullable=False),
        sa.Column("visitor_shoot_fee", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("sumup_fee_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data back from key-value table
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT `key`, value FROM setting")).mappings().all()
    kv = {r["key"]: r["value"] for r in rows}

    def _bool(v):
        return 1 if v and v.lower() in ("true", "1", "yes") else 0

    conn.execute(
        sa.text("""
            INSERT INTO application_settings (
                membership_year_start_month, membership_year_start_day,
                annual_membership_cost, membership_shoots_included,
                additional_shoot_cost, visitor_shoot_fee,
                news_enabled, events_enabled,
                cash_payment_instructions, sumup_fee_percentage,
                created_at, updated_at
            ) VALUES (
                :month, :day, :cost, :shoots, :additional, :visitor,
                :news, :events, :instructions, :sumup,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """),
        {
            "month": int(kv.get("membership_year_start_month", "3")),
            "day": int(kv.get("membership_year_start_day", "1")),
            "cost": int(kv.get("annual_membership_cost", "10000")),
            "shoots": int(kv.get("membership_shoots_included", "20")),
            "additional": int(kv.get("additional_shoot_cost", "500")),
            "visitor": int(kv.get("visitor_shoot_fee", "1000")),
            "news": _bool(kv.get("news_enabled")),
            "events": _bool(kv.get("events_enabled")),
            "instructions": kv.get(
                "cash_payment_instructions",
                "Please pay cash to a committee member at the next shoot night. "
                "Your membership/credits will be activated once payment is confirmed.",
            ),
            "sumup": kv.get("sumup_fee_percentage"),
        },
    )

    op.drop_table("setting")

