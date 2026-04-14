"""BotPool — manages N Bot + Dispatcher instances in one asyncio event loop (Card 19).

Polling mode (WEBHOOK_MODE=false): each bot runs its own start_polling() coroutine.
Hot registration: call pool.register(config) at runtime without a full restart.

Backward compatibility: when MULTI_BOT_ENABLED=false the single-bot main.py never
instantiates BotPool and the pool is unused.
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from bot.database import Database
from bot.database.models.main import BotConfig, Brand
from bot.multibot.instance import BotInstance

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Handler registration function is injected by main.py to avoid circular imports
_register_handlers_fn = None


def set_handler_registration_fn(fn) -> None:
    """Called by main.py to inject the handler-registration callback."""
    global _register_handlers_fn
    _register_handlers_fn = fn


class BotPool:
    """Manages multiple Bot / Dispatcher pairs in one asyncio event loop."""

    def __init__(self, storage=None):
        self._storage = storage or MemoryStorage()
        self._instances: dict[int, BotInstance] = {}   # brand_id → BotInstance
        self._tasks: dict[int, asyncio.Task] = {}       # brand_id → polling Task

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start_all(self) -> None:
        """Load all active BotConfigs from DB and start polling for each."""
        with Database().session() as s:
            configs = s.query(BotConfig).filter(BotConfig.is_active.is_(True)).all()
            s.expunge_all()

        if not configs:
            logger.warning("BotPool.start_all: no active BotConfig rows found in DB")
            return

        for cfg in configs:
            try:
                await self.register(cfg)
            except Exception as exc:
                logger.error("Failed to start bot for brand_id=%s: %s", cfg.brand_id, exc)

        logger.info("BotPool started %d bot(s)", len(self._instances))

    async def shutdown(self) -> None:
        """Gracefully stop all bots."""
        for brand_id in list(self._instances):
            await self.unregister(brand_id)
        logger.info("BotPool shutdown complete")

    # ── Registration ──────────────────────────────────────────────────────────

    async def register(self, config: BotConfig) -> BotInstance:
        """Start polling for one bot. Idempotent — silently replaces if already running."""
        if config.brand_id in self._instances:
            await self.unregister(config.brand_id)

        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(
                parse_mode="HTML",
                link_preview_is_disabled=False,
                protect_content=False,
            ),
        )

        dp = Dispatcher(storage=self._storage)

        # Inject brand context before any handler runs
        from bot.middleware.brand_context import BrandContextMiddleware
        mw = BrandContextMiddleware(config.brand_id)
        dp.message.middleware(mw)
        dp.callback_query.middleware(mw)
        dp.pre_checkout_query.middleware(mw)

        # Register the shared handler tree
        if _register_handlers_fn:
            _register_handlers_fn(dp)
        else:
            logger.warning("BotPool: no handler registration function set; bot will not respond")

        # Cache username from Telegram
        try:
            me = await bot.get_me()
            username = me.username or ""
        except Exception:
            username = ""

        # Persist cached metadata back to DB
        with Database().session() as s:
            db_cfg = s.query(BotConfig).filter(BotConfig.id == config.id).first()
            if db_cfg:
                db_cfg.bot_username = username
                db_cfg.bot_display_name = me.first_name if 'me' in dir() else None
                s.commit()

        instance = BotInstance(
            bot=bot,
            dp=dp,
            brand_id=config.brand_id,
            config_id=config.id,
            bot_username=username,
        )
        self._instances[config.brand_id] = instance

        task = asyncio.create_task(
            dp.start_polling(
                bot,
                allowed_updates=config.allowed_updates or [
                    "message", "callback_query", "pre_checkout_query", "successful_payment"
                ],
            ),
            name=f"poll-brand-{config.brand_id}",
        )
        self._tasks[config.brand_id] = task

        logger.info("Registered bot @%s for brand_id=%s", username, config.brand_id)
        return instance

    async def unregister(self, brand_id: int) -> None:
        """Stop polling and close session for one brand's bot."""
        task = self._tasks.pop(brand_id, None)
        instance = self._instances.pop(brand_id, None)

        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

        if instance:
            try:
                await instance.bot.session.close()
            except Exception:
                pass

        logger.info("Unregistered bot for brand_id=%s", brand_id)

    # ── Runtime helpers ───────────────────────────────────────────────────────

    def get_instance(self, brand_id: int) -> BotInstance | None:
        return self._instances.get(brand_id)

    def list_active(self) -> list[dict]:
        """Return a summary list of all running bots (for CLI/monitoring)."""
        return [
            {
                "brand_id": inst.brand_id,
                "username": inst.bot_username,
                "config_id": inst.config_id,
            }
            for inst in self._instances.values()
        ]

    # ── Class-level factory helpers ───────────────────────────────────────────

    @classmethod
    def ensure_default_brand(cls) -> int:
        """
        In single-bot (MULTI_BOT_ENABLED=false) mode, ensure a Brand row with id=1
        and a matching BotConfig row exist.  Returns the brand_id (always 1).
        This is called at startup so that BrandContextMiddleware always has a valid
        brand_id to inject even in legacy single-bot deployments.
        """
        from bot.config.env import EnvKeys
        with Database().session() as s:
            brand = s.query(Brand).filter(Brand.id == 1).first()
            if not brand:
                brand = Brand(name="Default", slug="default")
                s.add(brand)
                s.flush()

            cfg = s.query(BotConfig).filter(BotConfig.brand_id == brand.id).first()
            if not cfg:
                token = EnvKeys.TOKEN or "placeholder:token"
                cfg = BotConfig(brand_id=brand.id, bot_token=token, is_active=True)
                s.add(cfg)

            s.commit()
        return 1
