import asyncio

import pytest

from app.core.database import get_db


def test_get_db_yields_session_and_closes():
    async def _run():
        agen = get_db()
        session = await agen.__anext__()
        assert session is not None
        await agen.aclose()

    asyncio.run(_run())


def test_get_db_rolls_back_on_exception():
    async def _run():
        agen = get_db()
        await agen.__anext__()
        with pytest.raises(RuntimeError, match="boom"):
            await agen.athrow(RuntimeError("boom"))

    asyncio.run(_run())
