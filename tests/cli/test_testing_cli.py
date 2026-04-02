"""Tests for testing CLI commands (mocked os.system since they shell out)."""

from unittest.mock import patch


class TestTestRun:
    @patch("app.cli.testing.os.system", return_value=0)
    def test_run_basic(self, mock_system, runner):
        result = runner.invoke(args=["test", "run"])
        assert "Running:" in result.output
        mock_system.assert_called_once_with("pytest")

    @patch("app.cli.testing.os.system", return_value=0)
    def test_run_verbose(self, mock_system, runner):
        runner.invoke(args=["test", "run", "-v"])
        mock_system.assert_called_once_with("pytest -v")

    @patch("app.cli.testing.os.system", return_value=0)
    def test_run_with_coverage(self, mock_system, runner):
        runner.invoke(args=["test", "run", "-c"])
        cmd = mock_system.call_args[0][0]
        assert "--cov=app" in cmd
        assert "--cov-report=term-missing" in cmd

    @patch("app.cli.testing.os.system", return_value=0)
    def test_run_with_keyword(self, mock_system, runner):
        runner.invoke(args=["test", "run", "-k", "test_something"])
        cmd = mock_system.call_args[0][0]
        assert '-k "test_something"' in cmd

    @patch("app.cli.testing.os.system", return_value=0)
    def test_run_all_options(self, mock_system, runner):
        runner.invoke(args=["test", "run", "-v", "-c", "-k", "foo"])
        cmd = mock_system.call_args[0][0]
        assert "-v" in cmd
        assert "--cov=app" in cmd
        assert '-k "foo"' in cmd


class TestTestFile:
    @patch("app.cli.testing.os.system", return_value=0)
    def test_file_basic(self, mock_system, runner):
        result = runner.invoke(args=["test", "file", "tests/test_example.py"])
        assert "Running:" in result.output
        mock_system.assert_called_once_with("pytest tests/test_example.py")

    @patch("app.cli.testing.os.system", return_value=0)
    def test_file_verbose(self, mock_system, runner):
        runner.invoke(args=["test", "file", "tests/test_example.py", "-v"])
        cmd = mock_system.call_args[0][0]
        assert "tests/test_example.py" in cmd
        assert "-v" in cmd


class TestTestCoverage:
    @patch("app.cli.testing.os.system", return_value=0)
    def test_coverage(self, mock_system, runner):
        result = runner.invoke(args=["test", "coverage"])
        assert "Running tests with coverage" in result.output
        cmd = mock_system.call_args[0][0]
        assert "--cov=app" in cmd
        assert "--cov-report=html" in cmd
