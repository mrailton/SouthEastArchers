"""Tests for asset building CLI commands (mocked os.system since they shell out)."""

from unittest.mock import patch


class TestAssetsBuild:
    @patch("app.cli.assets.os.system", return_value=0)
    def test_build_success(self, mock_system, runner):
        result = runner.invoke(args=["assets", "build"])
        assert "Building production assets" in result.output
        assert "Assets built successfully!" in result.output
        mock_system.assert_called_once_with("npm run build")

    @patch("app.cli.assets.os.system", return_value=256)
    def test_build_failure(self, mock_system, runner):
        result = runner.invoke(args=["assets", "build"])
        assert "Building production assets" in result.output
        assert "Assets built successfully!" not in result.output


class TestAssetsWatch:
    @patch("app.cli.assets.os.system", return_value=0)
    def test_watch(self, mock_system, runner):
        result = runner.invoke(args=["assets", "watch"])
        assert "Starting Vite dev server" in result.output
        mock_system.assert_called_once_with("npm run dev")
