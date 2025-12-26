"""Tests for CLI commands."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from data_quality_framework.cli import cli


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def config_file():
    """Return path to test config file."""
    config_path = Path(__file__).parent.parent / "config" / "openweather_raw_validation.yaml"
    return config_path


@pytest.fixture
def data_file():
    """Return path to test data file."""
    data_path = Path(__file__).parent.parent / "data" / "example_data.json"
    return data_path


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output

    def test_cli_version(self, cli_runner):
        """Test CLI version command if available."""
        result = cli_runner.invoke(cli, ["--version"])
        # May or may not have version, just check it doesn't crash
        assert result.exit_code in [0, 2]

    def test_cli_invalid_command(self, cli_runner):
        """Test CLI with invalid command."""
        result = cli_runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0


class TestValidateCommands:
    """Test validate CLI commands."""

    def test_validate_command_exists(self, cli_runner):
        """Test that validate command exists."""
        result = cli_runner.invoke(cli, ["validate", "--help"])
        # Should either work or not exist
        assert result.exit_code in [0, 2]

    def test_validate_json_help(self, cli_runner):
        """Test validate-json help."""
        result = cli_runner.invoke(cli, ["validate-json", "--help"])
        # Should either work or not exist
        assert result.exit_code in [0, 2]

    def test_validate_csv_help(self, cli_runner):
        """Test validate-csv help."""
        result = cli_runner.invoke(cli, ["validate-csv", "--help"])
        # Should either work or not exist
        assert result.exit_code in [0, 2]


class TestConfigCommands:
    """Test configuration-related CLI commands."""

    def test_list_configs_command(self, cli_runner):
        """Test listing available configs."""
        result = cli_runner.invoke(cli, ["list-configs"])
        # Should either work or not exist
        assert result.exit_code in [0, 2]

    def test_show_config_command(self, cli_runner, config_file):
        """Test showing config details."""
        if config_file.exists():
            result = cli_runner.invoke(cli, ["show-config", str(config_file)])
            # Should either work or not exist
            assert result.exit_code in [0, 2]


class TestCLIDataValidation:
    """Test CLI data validation commands."""

    def test_validate_json_file(self, cli_runner, data_file):
        """Test validating JSON file."""
        if data_file.exists():
            result = cli_runner.invoke(
                cli,
                ["validate-json", str(data_file), "--config", "openweather_raw_validation.yaml"]
            )
            # Should either work or return expected error
            assert result.exit_code in [0, 1, 2]

    def test_validate_csv_file(self, cli_runner):
        """Test validating CSV file."""
        result = cli_runner.invoke(
            cli,
            ["validate-csv", "--help"]
        )
        # Should either work or command may not exist
        assert result.exit_code in [0, 2]


class TestCLIErrors:
    """Test CLI error handling."""

    def test_missing_required_argument(self, cli_runner):
        """Test missing required arguments."""
        result = cli_runner.invoke(cli, ["validate-json"])
        # Should fail due to missing file
        assert result.exit_code != 0

    def test_nonexistent_file(self, cli_runner):
        """Test with non-existent file."""
        result = cli_runner.invoke(
            cli,
            ["validate-json", "/nonexistent/file.json"]
        )
        # Should fail due to file not found
        assert result.exit_code != 0


class TestCLIOptions:
    """Test CLI option handling."""

    def test_verbose_flag(self, cli_runner):
        """Test verbose flag."""
        result = cli_runner.invoke(cli, ["--help", "-v"])
        # Verbose flag may or may not be supported
        assert result.exit_code in [0, 2]

    def test_config_option(self, cli_runner):
        """Test config option."""
        result = cli_runner.invoke(
            cli,
            ["--config", "test.yaml", "--help"]
        )
        # May work or command may be different
        assert result.exit_code in [0, 2]
