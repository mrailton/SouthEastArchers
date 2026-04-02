"""Tests for lint CLI commands (mocked os.system since they shell out)."""

from unittest.mock import patch


class TestLintCheck:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_check_passes(self, mock_system, runner):
        result = runner.invoke(args=["lint", "check"])
        assert "Running Ruff Linting" in result.output
        assert "Checking Code Format" in result.output
        assert "All checks passed!" in result.output
        assert mock_system.call_count == 2

    @patch("app.cli.lint.os.system", return_value=1)
    def test_lint_check_fails(self, mock_system, runner):
        result = runner.invoke(args=["lint", "check"])
        assert "Tip: Run 'flask lint fix'" in result.output


class TestLintFix:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_fix_passes(self, mock_system, runner):
        result = runner.invoke(args=["lint", "fix"])
        assert "Running Ruff Linting with --fix" in result.output
        assert "Formatting Code" in result.output
        assert "All issues fixed!" in result.output

    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_fix_calls_ruff_with_fix_flag(self, mock_system, runner):
        runner.invoke(args=["lint", "fix"])
        calls = [str(c) for c in mock_system.call_args_list]
        assert any("--fix" in c for c in calls)


class TestLintFormat:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_format_check_mode(self, mock_system, runner):
        result = runner.invoke(args=["lint", "format", "--check"])
        assert "Checking code format" in result.output
        calls = [str(c) for c in mock_system.call_args_list]
        assert any("--check" in c for c in calls)

    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_format_write_mode(self, mock_system, runner):
        result = runner.invoke(args=["lint", "format"])
        assert "Formatting code" in result.output
        assert "Code formatted!" in result.output


class TestLintAll:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_all_passes(self, mock_system, runner):
        result = runner.invoke(args=["lint", "all"])
        assert "Running Ruff Linting" in result.output
        assert "Running Ruff Format" in result.output
        assert "Checking Module Boundaries" in result.output
        assert "All checks passed!" in result.output
        assert mock_system.call_count == 3

    @patch("app.cli.lint.os.system", return_value=0)
    def test_lint_all_fix_mode(self, mock_system, runner):
        runner.invoke(args=["lint", "all", "--fix"])
        calls = [str(c) for c in mock_system.call_args_list]
        assert any("--fix" in c for c in calls)

    @patch("app.cli.lint.os.system", return_value=1)
    def test_lint_all_failure_shows_tip(self, mock_system, runner):
        result = runner.invoke(args=["lint", "all"])
        assert "Tip:" in result.output


class TestLintTypecheck:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_typecheck_passes(self, mock_system, runner):
        result = runner.invoke(args=["lint", "typecheck"])
        assert "Running mypy" in result.output
        assert "Type checking passed!" in result.output
        mock_system.assert_called_once_with("mypy app/")

    @patch("app.cli.lint.os.system", return_value=256)
    def test_typecheck_fails(self, mock_system, runner):
        result = runner.invoke(args=["lint", "typecheck"])
        assert "Type checking passed!" not in result.output


class TestLintImports:
    @patch("app.cli.lint.os.system", return_value=0)
    def test_imports_check_passes(self, mock_system, runner):
        result = runner.invoke(args=["lint", "imports"])
        assert "Checking module boundaries" in result.output
        assert "Module boundary checks passed!" in result.output
        mock_system.assert_called_once_with("lint-imports")
