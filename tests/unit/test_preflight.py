"""Tests for the preflight check system."""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from bot.preflight import (
    PreflightReport, CheckResult,
    _check_env_vars, _check_database, _check_redis, _check_monitoring_port,
)


@pytest.mark.unit
class TestPreflightReport:
    """Test the report data structure."""

    def test_empty_report_ok(self):
        report = PreflightReport()
        assert report.ok is True
        assert len(report.checks) == 0

    def test_pass_only(self):
        report = PreflightReport()
        report.add("A", "pass", "good")
        report.add("B", "pass", "fine")
        assert report.ok is True
        assert len(report.passed) == 2
        assert len(report.failures) == 0

    def test_warn_does_not_fail(self):
        report = PreflightReport()
        report.add("A", "pass", "good")
        report.add("B", "warn", "not great", required=False)
        assert report.ok is True
        assert len(report.warnings) == 1

    def test_required_fail(self):
        report = PreflightReport()
        report.add("A", "pass", "good")
        report.add("B", "fail", "broken", required=True)
        assert report.ok is False
        assert len(report.failures) == 1

    def test_optional_fail_still_ok(self):
        report = PreflightReport()
        report.add("A", "pass", "good")
        report.add("B", "fail", "broken", required=False)
        assert report.ok is True  # Optional failures don't block


@pytest.mark.unit
class TestEnvVarChecks:
    """Test environment variable validation."""

    def test_valid_env(self):
        report = PreflightReport()
        _check_env_vars(report)
        # TOKEN is set to test value by conftest
        token_check = next(c for c in report.checks if c.name == "TOKEN")
        assert token_check.status == "pass"

    def test_owner_id_set(self):
        report = PreflightReport()
        _check_env_vars(report)
        owner_check = next(c for c in report.checks if c.name == "OWNER_ID")
        assert owner_check.status == "pass"

    def test_locale_check(self):
        report = PreflightReport()
        _check_env_vars(report)
        locale_check = next(c for c in report.checks if c.name == "BOT_LOCALE")
        # BOT_LOCALE defaults to "th" which is valid
        assert locale_check.status in ("pass", "warn")

    def test_kitchen_rider_groups(self):
        report = PreflightReport()
        _check_env_vars(report)
        kitchen = next((c for c in report.checks if c.name == "KITCHEN_GROUP_ID"), None)
        assert kitchen is not None
        assert kitchen.required is False

    def test_slip_verification(self):
        report = PreflightReport()
        _check_env_vars(report)
        slip = next((c for c in report.checks if c.name == "SLIP_VERIFICATION"), None)
        assert slip is not None
        assert slip.required is False


@pytest.mark.unit
class TestDatabaseCheck:
    """Test database connectivity check."""

    def test_database_connectable(self):
        """Should pass since test fixtures set up SQLite."""
        report = PreflightReport()
        _check_database(report)
        db_check = next(c for c in report.checks if c.name == "Database")
        # In test env, SQLite is used — should find tables
        assert db_check.status in ("pass", "warn")

    def test_database_has_core_tables(self):
        report = PreflightReport()
        _check_database(report)
        db_check = next(c for c in report.checks if c.name == "Database")
        assert "tables" in db_check.message.lower() or "connect" in db_check.message.lower()


@pytest.mark.unit
class TestRedisCheck:
    """Test Redis connectivity check."""

    def test_redis_check_runs(self):
        """Redis check should produce a result without crashing."""
        report = PreflightReport()
        _check_redis(report)
        redis_check = next(c for c in report.checks if c.name == "Redis")
        # In test env Redis may or may not be available
        assert redis_check.status in ("pass", "warn")
        assert redis_check.required is False


@pytest.mark.unit
class TestMonitoringPortCheck:
    """Test monitoring port availability check."""

    def test_port_check_runs(self):
        report = PreflightReport()
        _check_monitoring_port(report)
        port_check = next(c for c in report.checks if c.name == "Monitoring Port")
        assert port_check.status in ("pass", "warn")
        assert port_check.required is False


@pytest.mark.unit
class TestPreflightIntegration:
    """Test the full preflight flow."""

    @pytest.mark.asyncio
    async def test_run_preflight(self):
        from bot.preflight import run_preflight, _check_env_vars, _check_database, _check_redis, _check_monitoring_port, PreflightReport

        # Run only sync checks (Telegram API needs real token)
        report = PreflightReport()
        _check_env_vars(report)
        _check_database(report)
        _check_redis(report)
        _check_monitoring_port(report)

        # Should have run multiple checks
        assert len(report.checks) >= 8

        # TOKEN and OWNER_ID are set in test env
        token = next(c for c in report.checks if c.name == "TOKEN")
        assert token.status == "pass"

        # Report should log without errors
        report.log_report()
