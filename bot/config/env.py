import os
from abc import ABC
from typing import Final


class EnvKeys(ABC):
    """Secure environment configuration with validation"""

    # Telegram
    TOKEN: Final = os.environ.get('TOKEN')
    OWNER_ID: Final = os.environ.get('OWNER_ID')

    PAY_CURRENCY: Final = os.getenv("PAY_CURRENCY", "THB")
    MIN_AMOUNT: Final = int(os.getenv("MIN_AMOUNT", 20))
    MAX_AMOUNT: Final = int(os.getenv("MAX_AMOUNT", 10_000))

    # Links / UI
    CHANNEL_URL: Final = os.getenv("CHANNEL_URL")
    HELPER_ID: Final = os.getenv("HELPER_ID")
    RULES: Final = os.getenv("RULES")

    # Locale & logs
    BOT_LOCALE: Final = os.getenv("BOT_LOCALE", "th")
    BOT_LOGFILE: Final = os.getenv("BOT_LOGFILE", "logs/bot.log")
    BOT_AUDITFILE: Final = os.getenv("BOT_AUDITFILE", "logs/audit.log")
    LOG_TO_STDOUT: Final = os.getenv("LOG_TO_STDOUT", "1")
    LOG_TO_FILE: Final = os.getenv("LOG_TO_FILE", "1")
    DEBUG: Final = os.getenv("DEBUG", "0")

    # Redis
    REDIS_HOST: Final = os.getenv("REDIS_HOST")
    REDIS_PORT: Final = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: Final = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Final = os.getenv("REDIS_PASSWORD")

    # Database (for Docker)
    POSTGRES_DB: Final = os.getenv("POSTGRES_DB")
    POSTGRES_USER: Final = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: Final = os.getenv("POSTGRES_PASSWORD")
    DB_PORT: Final = int(os.getenv("DB_PORT", 5432))
    DB_DRIVER: Final = os.getenv("DB_DRIVER", "postgresql+psycopg2")

    # PromptPay (Card 1)
    PROMPTPAY_ID: Final = os.getenv("PROMPTPAY_ID")  # Phone number or national ID
    PROMPTPAY_ACCOUNT_NAME: Final = os.getenv("PROMPTPAY_ACCOUNT_NAME", "")

    # Slip Verification — Thai Slip Verification Services
    # Configure one or more. Tried in order: SlipOK → EasySlip → RDCW
    SLIPOK_API_KEY: Final = os.getenv("SLIPOK_API_KEY")
    SLIPOK_BRANCH_ID: Final = os.getenv("SLIPOK_BRANCH_ID")
    EASYSLIP_API_KEY: Final = os.getenv("EASYSLIP_API_KEY")
    RDCW_CLIENT_ID: Final = os.getenv("RDCW_CLIENT_ID")
    RDCW_CLIENT_SECRET: Final = os.getenv("RDCW_CLIENT_SECRET")
    SLIP_AUTO_VERIFY: Final = os.getenv("SLIP_AUTO_VERIFY", "1")  # 1=auto-verify, 0=manual only

    # Kitchen & Delivery Groups (Card 9)
    KITCHEN_GROUP_ID: Final = os.getenv("KITCHEN_GROUP_ID")
    RIDER_GROUP_ID: Final = os.getenv("RIDER_GROUP_ID")

    # Delivery chat (Card 15)
    POST_DELIVERY_CHAT_MINUTES: Final = int(os.getenv("POST_DELIVERY_CHAT_MINUTES", 30))

    # Support / Maintainer (live chat)
    SUPPORT_CHAT_ID: Final = os.getenv("SUPPORT_CHAT_ID")  # Group/channel ID where support staff monitor
    MAINTAINER_IDS: Final = os.getenv("MAINTAINER_IDS", "")  # Comma-separated Telegram IDs of app maintainers

    # Grok AI Assistant (Card 17)
    GROK_API_KEY: Final = os.getenv("GROK_API_KEY", "")
    GROK_MODEL: Final = os.getenv("GROK_MODEL", "grok-3-mini")
    GROK_TIMEOUT: Final = int(os.getenv("GROK_TIMEOUT", 30))

    # PDPA Privacy Policy
    PRIVACY_POLICY_URL: Final = os.getenv("PRIVACY_POLICY_URL", "")
    PRIVACY_CONTACT_EMAIL: Final = os.getenv("PRIVACY_CONTACT_EMAIL", "")
    PRIVACY_COMPANY_NAME: Final = os.getenv("PRIVACY_COMPANY_NAME", "")

    # Monitoring
    MONITORING_HOST: Final = os.getenv("MONITORING_HOST", "localhost")
    MONITORING_PORT: Final = int(os.getenv("MONITORING_PORT", 9090))

    # Database (for manual deploy) — SEC-02 fix: require env var, no hardcoded credentials
    DATABASE_URL: Final = os.environ.get("DATABASE_URL")  # must be set in environment
