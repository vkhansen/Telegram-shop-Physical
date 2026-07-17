"""
Preflight Check System.

Runs at bot startup to verify all env vars, services, and API keys
are properly configured and reachable before accepting traffic.

Checks:
 1. Required env vars are set (TOKEN, OWNER_ID, database creds)
 2. Telegram Bot API is reachable and token is valid
 3. PostgreSQL database is connectable and tables exist
 4. Redis is connectable (if configured)
 5. PromptPay ID format is valid (if configured)
 6. Slip verification API keys are valid (if configured)
 7. Kitchen/Rider group IDs are reachable (if configured)
 8. Support/maintainer IDs are set (if support enabled)
 9. Timezone is valid
10. Locale is valid
11. Monitoring port is available
"""

import logging
import os
import socket
from dataclasses import dataclass, field
from typing import Literal

from bot.config.env import EnvKeys

logger = logging.getLogger(__name__)

Status = Literal["pass", "warn", "fail"]


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    required: bool = True


@dataclass
class PreflightReport:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, status: Status, message: str, required: bool = True):
        self.checks.append(CheckResult(name=name, status=status, message=message, required=required))

    @property
    def passed(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "pass"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "warn"]

    @property
    def failures(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "fail" and c.required]

    @property
    def ok(self) -> bool:
        return len(self.failures) == 0

    def log_report(self):
        len(self.checks)
        passed = len(self.passed)
        warns = len(self.warnings)
        fails = len(self.failures)

        logger.info("=" * 60)
        logger.info("  PREFLIGHT CHECK REPORT")
        logger.info("=" * 60)

        for check in self.checks:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[check.status]
            req = "" if check.required else " (optional)"
            logger.info(f"  {icon} {check.name}{req}: {check.message}")

        logger.info("-" * 60)
        logger.info(f"  Result: {passed} passed, {warns} warnings, {fails} failures")

        if not self.ok:
            logger.critical(f"  ❌ PREFLIGHT FAILED — {fails} required check(s) did not pass")
        else:
            logger.info("  ✅ ALL REQUIRED CHECKS PASSED")
        logger.info("=" * 60)


def _web_api_only() -> bool:
    """When set, only the HTTP public API / monitoring surface is required (no Telegram)."""
    return os.getenv("WEB_API_ONLY", "").lower() in ("1", "true", "yes")


def _check_env_vars(report: PreflightReport):
    """Check required and optional environment variables."""

    api_only = _web_api_only()
    if api_only:
        report.add(
            "WEB_API_ONLY",
            "pass",
            "Enabled — Telegram token/polling not required; HTTP API only",
            required=False,
        )

    # Required for full bot; optional when WEB_API_ONLY=1 (Funnel / storefront testing)
    if not EnvKeys.TOKEN:
        report.add(
            "TOKEN",
            "warn" if api_only else "fail",
            "Not set — bot cannot poll Telegram without a token",
            required=not api_only,
        )
    elif EnvKeys.TOKEN == "your_bot_token_here":  # noqa: S105 — placeholder/marker string, not a secret
        report.add(
            "TOKEN",
            "warn" if api_only else "fail",
            "Still set to placeholder value from .env.example",
            required=not api_only,
        )
    else:
        # Telegram tokens are "<numeric_bot_id>:<secret>"
        parts = EnvKeys.TOKEN.split(":", 1)
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
            report.add(
                "TOKEN",
                "warn" if api_only else "fail",
                "Invalid format — expected <numeric_bot_id>:<secret> from @BotFather",
                required=not api_only,
            )
        else:
            report.add("TOKEN", "pass", f"Set ({len(EnvKeys.TOKEN)} chars)")

    if not EnvKeys.OWNER_ID:
        report.add(
            "OWNER_ID",
            "warn" if api_only else "fail",
            "Not set — no admin can manage the bot",
            required=not api_only,
        )
    else:
        try:
            int(EnvKeys.OWNER_ID)
            report.add("OWNER_ID", "pass", f"Set ({EnvKeys.OWNER_ID})")
        except ValueError:
            report.add(
                "OWNER_ID",
                "warn" if api_only else "fail",
                f"Invalid — must be a number, got '{EnvKeys.OWNER_ID}'",
                required=not api_only,
            )

    # Database
    if os.getenv("POSTGRES_HOST") or os.path.exists("/.dockerenv"):
        os.getenv("POSTGRES_USER")
        db_pass = os.getenv("POSTGRES_PASSWORD")
        db_name = os.getenv("POSTGRES_DB")
        if not db_pass or db_pass == "change_me_to_strong_password":  # noqa: S105 — placeholder/marker string, not a secret
            report.add("POSTGRES_PASSWORD", "warn", "Using default/weak password")
        else:
            report.add("POSTGRES_PASSWORD", "pass", "Set")
        if db_name:
            report.add("POSTGRES_DB", "pass", f"Database: {db_name}")
        else:
            report.add("POSTGRES_DB", "warn", "Not set, using default 'telegram_shop'")
    else:
        report.add("DATABASE_URL", "pass", "Using local development DSN")

    # Optional but important
    if EnvKeys.PROMPTPAY_ID:
        ppid = EnvKeys.PROMPTPAY_ID
        if len(ppid) == 10 and ppid.isdigit():
            report.add("PROMPTPAY_ID", "pass", f"Phone format ({ppid[:3]}***)", required=False)
        elif len(ppid) == 13 and ppid.isdigit():
            report.add("PROMPTPAY_ID", "pass", "National ID format", required=False)
        else:
            report.add("PROMPTPAY_ID", "warn", f"Unusual format: '{ppid}' (expected 10 or 13 digits)", required=False)
    else:
        report.add("PROMPTPAY_ID", "warn", "Not set — PromptPay payments disabled", required=False)

    # Locale
    from bot.i18n.strings import AVAILABLE_LOCALES

    bot_locale = EnvKeys.BOT_LOCALE
    if bot_locale in AVAILABLE_LOCALES:
        report.add("BOT_LOCALE", "pass", f"{bot_locale} ({AVAILABLE_LOCALES[bot_locale]})")
    else:
        report.add("BOT_LOCALE", "warn", f"'{bot_locale}' not in available locales, will fallback to 'th'")

    # Timezone
    tz = os.getenv("TIMEZONE", "Asia/Bangkok")
    try:
        import pytz

        pytz.timezone(tz)
        report.add("TIMEZONE", "pass", tz)
    except Exception:
        report.add("TIMEZONE", "warn", f"'{tz}' — could not validate (pytz not available or invalid)")

    # Groups
    if EnvKeys.KITCHEN_GROUP_ID:
        report.add("KITCHEN_GROUP_ID", "pass", f"Set ({EnvKeys.KITCHEN_GROUP_ID})", required=False)
    else:
        report.add("KITCHEN_GROUP_ID", "warn", "Not set — kitchen notifications disabled", required=False)

    if EnvKeys.RIDER_GROUP_ID:
        report.add("RIDER_GROUP_ID", "pass", f"Set ({EnvKeys.RIDER_GROUP_ID})", required=False)
    else:
        report.add("RIDER_GROUP_ID", "warn", "Not set — rider notifications disabled", required=False)

    # Support
    maintainer_ids = EnvKeys.MAINTAINER_IDS or ""
    support_chat = EnvKeys.SUPPORT_CHAT_ID
    if maintainer_ids.strip():
        report.add("MAINTAINER_IDS", "pass", f"Set ({maintainer_ids})", required=False)
    else:
        report.add("MAINTAINER_IDS", "warn", "Not set — will fallback to OWNER_ID for support", required=False)
    if support_chat:
        report.add("SUPPORT_CHAT_ID", "pass", f"Set ({support_chat})", required=False)
    else:
        report.add("SUPPORT_CHAT_ID", "warn", "Not set — support messages only sent to maintainer DMs", required=False)

    # Slip verification
    has_slip = bool(EnvKeys.SLIPOK_API_KEY or EnvKeys.EASYSLIP_API_KEY or EnvKeys.RDCW_CLIENT_ID)
    if has_slip:
        providers = []
        if EnvKeys.SLIPOK_API_KEY:
            providers.append("SlipOK")
        if EnvKeys.EASYSLIP_API_KEY:
            providers.append("EasySlip")
        if EnvKeys.RDCW_CLIENT_ID:
            providers.append("RDCW")
        report.add("SLIP_VERIFICATION", "pass", f"Providers: {', '.join(providers)}", required=False)
    else:
        report.add("SLIP_VERIFICATION", "warn", "No slip verification API keys — manual review only", required=False)


async def _check_telegram_api(report: PreflightReport):
    """Verify Telegram Bot API token is valid."""
    if not EnvKeys.TOKEN or EnvKeys.TOKEN == "your_bot_token_here":  # noqa: S105 — placeholder/marker string, not a secret
        return  # Already reported in env check

    api_only = _web_api_only()
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.utils.token import TokenValidationError

        bot = Bot(token=EnvKeys.TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
        try:
            me = await bot.get_me()
            report.add("Telegram API", "pass", f"Bot: @{me.username} (ID: {me.id})")
        finally:
            await bot.session.close()
    except TokenValidationError:
        report.add(
            "Telegram API",
            "warn" if api_only else "fail",
            "TOKEN format is invalid — expected <numeric_bot_id>:<secret> from @BotFather",
            required=not api_only,
        )
    except Exception as e:
        err = str(e)[:100]
        status: Status = "warn" if api_only else "fail"
        if "Unauthorized" in err:
            report.add("Telegram API", status, "Token is invalid (401 Unauthorized)", required=not api_only)
        elif "Network" in err or "Cannot connect" in err:
            report.add(
                "Telegram API",
                status,
                f"Cannot reach api.telegram.org: {err}",
                required=not api_only,
            )
        else:
            report.add("Telegram API", status, f"Error: {err}", required=not api_only)


def _check_database(report: PreflightReport):
    """Verify PostgreSQL is connectable and has tables."""
    try:
        from sqlalchemy import inspect

        from bot.database.main import Database

        db = Database()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        expected = {"users", "roles", "orders", "goods", "categories"}
        expected & set(tables)
        missing = expected - set(tables)

        if missing:
            report.add("Database", "warn", f"Connected but missing tables: {missing}")
        else:
            report.add("Database", "pass", f"Connected — {len(tables)} tables found")
    except Exception as e:
        err = str(e)[:120]
        if "could not translate host name" in err or "Connection refused" in err:
            report.add("Database", "fail", f"Cannot connect to PostgreSQL: {err}")
        else:
            report.add("Database", "fail", f"Database error: {err}")


def _check_data_integrity(report: PreflightReport):
    """Report brand/store/menu integrity violations (non-blocking)."""
    try:
        from bot.database.integrity import check_integrity, summarize
        from bot.database.main import Database

        with Database().session() as session:
            violations = check_integrity(session)
        s = summarize(violations)
        if s["errors"]:
            sample = "; ".join(str(v.detail) for v in violations[:3])
            report.add(
                "Data Integrity",
                "warn",
                f"{s['errors']} error(s), {s['warnings']} warning(s) — run scripts/validate_data.py (e.g. {sample})",
                required=False,
            )
        elif s["warnings"]:
            report.add(
                "Data Integrity", "warn", f"{s['warnings']} warning(s) — run scripts/validate_data.py", required=False
            )
        else:
            report.add("Data Integrity", "pass", "No orphans or broken configs", required=False)
    except Exception as e:
        report.add("Data Integrity", "warn", f"Could not check: {str(e)[:80]}", required=False)


def _check_redis(report: PreflightReport):
    """Verify Redis is connectable (if configured)."""
    if not EnvKeys.REDIS_HOST:
        report.add("Redis", "warn", "Not configured — using MemoryStorage (FSM state lost on restart)", required=False)
        return

    try:
        import redis

        r = redis.Redis(
            host=EnvKeys.REDIS_HOST,
            port=EnvKeys.REDIS_PORT,
            db=EnvKeys.REDIS_DB,
            password=EnvKeys.REDIS_PASSWORD or None,
            socket_connect_timeout=5,
        )
        r.ping()
        info = r.info("server")
        version = info.get("redis_version", "unknown")
        report.add("Redis", "pass", f"Connected — Redis {version} at {EnvKeys.REDIS_HOST}:{EnvKeys.REDIS_PORT}")
        r.close()
    except ImportError:
        report.add("Redis", "warn", "redis-py not installed — using MemoryStorage", required=False)
    except Exception as e:
        report.add("Redis", "warn", f"Cannot connect: {str(e)[:80]} — falling back to MemoryStorage", required=False)


def _check_monitoring_port(report: PreflightReport):
    """Check if the monitoring port is available."""
    host = EnvKeys.MONITORING_HOST
    port = EnvKeys.MONITORING_PORT
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host if host != "0.0.0.0" else "127.0.0.1", port))
        sock.close()
        if result == 0:
            report.add(
                "Monitoring Port", "warn", f"Port {port} already in use — monitoring may fail to start", required=False
            )
        else:
            report.add("Monitoring Port", "pass", f"{host}:{port} available", required=False)
    except Exception:
        report.add("Monitoring Port", "pass", f"{host}:{port} (could not verify)", required=False)


async def _check_telegram_groups(report: PreflightReport):
    """Verify kitchen/rider groups are accessible (if configured)."""
    if not EnvKeys.TOKEN or EnvKeys.TOKEN == "your_bot_token_here":  # noqa: S105 — placeholder/marker string, not a secret
        return
    if not EnvKeys.KITCHEN_GROUP_ID and not EnvKeys.RIDER_GROUP_ID:
        return

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.utils.token import TokenValidationError

    try:
        bot = Bot(token=EnvKeys.TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    except TokenValidationError:
        # Token format already failed (or will fail) Telegram API check — don't crash preflight
        report.add(
            "Telegram Groups",
            "warn",
            "Skipped — TOKEN format is invalid (expected <numeric_bot_id>:<secret>)",
            required=False,
        )
        return
    except Exception as e:
        report.add("Telegram Groups", "warn", f"Skipped — cannot init Bot: {str(e)[:80]}", required=False)
        return

    try:
        for name, group_id in [("Kitchen Group", EnvKeys.KITCHEN_GROUP_ID), ("Rider Group", EnvKeys.RIDER_GROUP_ID)]:
            if not group_id:
                continue
            try:
                chat = await bot.get_chat(int(group_id))
                report.add(name, "pass", f"Accessible: {chat.title or chat.id}", required=False)
            except Exception as e:
                err = str(e)[:80]
                report.add(name, "warn", f"Cannot access group {group_id}: {err}", required=False)
    finally:
        await bot.session.close()


def _check_web_oauth(report: PreflightReport) -> None:
    """CARD-39: optional Google OAuth + session secrets for white-label portal."""
    site = (os.getenv("PUBLIC_SITE_URL") or "").strip()
    if site:
        report.add("PUBLIC_SITE_URL", "pass", site, required=False)
    else:
        report.add(
            "PUBLIC_SITE_URL",
            "warn",
            "Not set — OAuth callback redirects default to http://127.0.0.1:4321",
            required=False,
        )

    secret = (os.getenv("WEB_SESSION_SECRET") or "").strip()
    if not secret:
        report.add(
            "WEB_SESSION_SECRET",
            "warn",
            "Not set — sessions fall back to TOKEN (rotate before production)",
            required=False,
        )
    elif secret in ("change-me", "local-dev-session-secret", "dev-insecure-session-secret"):
        report.add(
            "WEB_SESSION_SECRET",
            "warn",
            "Using weak/dev placeholder — set a long random secret for production",
            required=False,
        )
    else:
        report.add("WEB_SESSION_SECRET", "pass", f"Set ({len(secret)} chars)", required=False)

    g_id = (os.getenv("OAUTH_GOOGLE_CLIENT_ID") or "").strip()
    g_sec = (os.getenv("OAUTH_GOOGLE_CLIENT_SECRET") or "").strip()
    redir = (os.getenv("OAUTH_GOOGLE_REDIRECT_URI") or "").strip()
    if g_id and g_sec:
        msg = "Google OAuth client configured"
        if redir:
            msg += f" · redirect {redir}"
        elif site:
            msg += f" · redirect defaults to {site.rstrip('/')}/api/public/auth/google/callback"
        else:
            msg += " · set OAUTH_GOOGLE_REDIRECT_URI for production"
        report.add("OAUTH_GOOGLE", "pass", msg, required=False)
    elif g_id or g_sec:
        report.add(
            "OAUTH_GOOGLE",
            "warn",
            "Partial Google OAuth env (need both CLIENT_ID and CLIENT_SECRET)",
            required=False,
        )
    else:
        report.add(
            "OAUTH_GOOGLE",
            "warn",
            "Not configured — storefront login uses dev login only (OAUTH_DEV_LOGIN)",
            required=False,
        )

    dev = os.getenv("OAUTH_DEV_LOGIN", "").lower() in ("1", "true", "yes")
    if dev and g_id and g_sec:
        report.add(
            "OAUTH_DEV_LOGIN",
            "warn",
            "true while Google is configured — disable in production",
            required=False,
        )
    elif dev:
        report.add("OAUTH_DEV_LOGIN", "pass", "Enabled (local/dev only)", required=False)

    secure = os.getenv("WEB_COOKIE_SECURE", "").lower() in ("1", "true", "yes")
    if site.startswith("https://") and not secure:
        report.add(
            "WEB_COOKIE_SECURE",
            "warn",
            "PUBLIC_SITE_URL is HTTPS but WEB_COOKIE_SECURE is off — set true for Funnel/prod",
            required=False,
        )
    elif secure:
        report.add("WEB_COOKIE_SECURE", "pass", "Session cookies marked Secure", required=False)


async def run_preflight() -> PreflightReport:
    """
    Run all preflight checks and return a report.

    Call this at bot startup before accepting traffic.
    Returns a PreflightReport — check report.ok to determine if the bot should start.
    """
    report = PreflightReport()

    logger.info("Running preflight checks...")

    # Sync checks
    _check_env_vars(report)
    _check_web_oauth(report)
    _check_database(report)
    _check_data_integrity(report)
    _check_redis(report)
    _check_monitoring_port(report)

    # Async checks (Telegram API)
    await _check_telegram_api(report)
    await _check_telegram_groups(report)

    report.log_report()
    return report
