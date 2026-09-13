"""
Unit tests for Tarkyaan CLI and runtime entry point.
"""

from unittest.mock import patch

from tarkyaan.__main__ import check_runtime_health, main


class TestTarkyaanCLI:
    def test_check_runtime_health_succeeds(self):
        status_code = check_runtime_health()
        assert status_code == 0

    def test_cli_main_status_flag(self):
        with patch("sys.argv", ["tarkyaan", "--status"]):
            exit_code = main()
            assert exit_code == 0

    def test_cli_main_default_invocation(self):
        with patch("sys.argv", ["tarkyaan"]):
            exit_code = main()
            assert exit_code == 0
