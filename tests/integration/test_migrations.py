"""Smoke tests that verify Alembic migrations apply cleanly on MySQL."""

from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register models
from app.models.rbac import seed_rbac


def _mysql_url() -> str | None:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if url and url.startswith("mysql"):
        return url
    return None


@pytest.fixture(scope="module")
def migrated_mysql():
    url = _mysql_url()
    if not url:
        pytest.skip("Migration smoke tests require MySQL TEST_DATABASE_URL")

    from app.core.config import PROJECT_ROOT

    cfg = Config(str(PROJECT_ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


def test_payments_external_transaction_id_index_is_unique(migrated_mysql):
    inspector = inspect(migrated_mysql)
    indexes = inspector.get_indexes("payments")
    ext_idx = next(i for i in indexes if "external_transaction_id" in i["column_names"])
    assert ext_idx["unique"] is True


def test_financial_transactions_composite_unique_exists(migrated_mysql):
    inspector = inspect(migrated_mysql)
    unique_constraints = inspector.get_unique_constraints("financial_transactions")
    names = {constraint["name"] for constraint in unique_constraints}
    assert "uq_financial_txn_receipt_category_type" in names


def test_payments_has_sumup_checkout_id_column(migrated_mysql):
    inspector = inspect(migrated_mysql)
    columns = {column["name"] for column in inspector.get_columns("payments")}
    assert "sumup_checkout_id" in columns


def test_migrated_schema_supports_rbac_seed(migrated_mysql):
    session = sessionmaker(bind=migrated_mysql)()
    try:
        seed_rbac(session)
        session.commit()
        role_count = session.execute(text("SELECT COUNT(*) FROM roles")).scalar()
        assert role_count is not None
        assert role_count >= 1
    finally:
        session.close()
