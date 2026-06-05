from unittest.mock import patch

from app.cli import cli
from tests.helpers import create_payment_for_user


@patch("app.services.payments.replay_payment_side_effects")
def test_replay_side_effects_cli_success(mock_replay, runner, app, test_user):
    from app import db
    from app.services.result import ServiceResult

    payment = create_payment_for_user(db, test_user, status="completed", payment_type="membership")
    mock_replay.return_value = ServiceResult.ok(message="Payment side effects replayed successfully.")

    result = runner.invoke(cli, ["payments", "replay-side-effects", str(payment.id)])

    assert result.exit_code == 0
    assert "replayed successfully" in result.output
    mock_replay.assert_called_once_with(payment.id, send_mail=True)


@patch("app.services.payments.replay_payment_side_effects")
def test_replay_side_effects_cli_no_mail(mock_replay, runner, app, test_user):
    from app import db
    from app.services.result import ServiceResult

    payment = create_payment_for_user(db, test_user, status="completed", payment_type="membership")
    mock_replay.return_value = ServiceResult.ok(message="ok")

    result = runner.invoke(cli, ["payments", "replay-side-effects", str(payment.id), "--no-mail"])

    assert result.exit_code == 0
    mock_replay.assert_called_once_with(payment.id, send_mail=False)
