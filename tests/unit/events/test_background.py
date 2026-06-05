from unittest.mock import patch

import pytest

from app.events.background import (
    defer_handler,
    flush_deferred_handlers,
    run_handler_safe,
    run_handler_with_session,
    take_deferred_handlers,
)


def test_defer_handler_queues_and_take_clears():
    seen: list[int] = []

    def handler(value: int) -> None:
        seen.append(value)

    defer_handler(handler, 42)
    queued = take_deferred_handlers()

    assert len(queued) == 1
    assert take_deferred_handlers() == []

    queued[0][0](*queued[0][1], **queued[0][2])
    assert seen == [42]


def test_flush_deferred_handlers_runs_queued_handlers(app):
    seen: list[str] = []

    def handler(message: str) -> None:
        seen.append(message)

    defer_handler(handler, "hello")
    flush_deferred_handlers()

    assert seen == ["hello"]
    assert take_deferred_handlers() == []


def test_run_handler_with_session_commits_and_closes(app):
    from app.db.session import has_current_session

    observed: list[bool] = []

    def handler() -> None:
        observed.append(has_current_session())

    run_handler_with_session(handler)

    assert observed == [True]


def test_run_handler_with_session_rolls_back_on_error(app):
    def handler() -> None:
        raise RuntimeError("handler failed")

    with pytest.raises(RuntimeError, match="handler failed"):
        run_handler_with_session(handler)


def test_run_handler_safe_runs_with_active_session(app):
    called: list[bool] = []

    def handler() -> None:
        called.append(True)

    run_handler_safe(handler)

    assert called == [True]


def test_run_handler_safe_logs_handler_failure(app, caplog):
    def handler() -> None:
        raise RuntimeError("boom")

    run_handler_safe(handler)

    assert "boom" in caplog.text or "failed" in caplog.text.lower()


def test_run_handler_safe_without_active_session(app):
    called: list[bool] = []

    def handler() -> None:
        called.append(True)

    with patch("app.db.session.has_current_session", return_value=False):
        with patch("app.events.background.run_handler_with_session", side_effect=lambda h, *a, **k: h()) as mock_run:
            run_handler_safe(handler)
            mock_run.assert_called_once_with(handler)

    assert called == [True]
