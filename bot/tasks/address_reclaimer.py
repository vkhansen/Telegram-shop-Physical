"""Reclaim crypto addresses for expired/cancelled orders (Card 24).

Used crypto addresses were previously never returned to the pool — it only
depleted, eventually producing the live "address pool running low" warning.
This task periodically releases addresses whose order ended without payment
(``expired`` / ``cancelled``) once a TTL has passed, so the pool replenishes.

The TTL grace period guards against a late on-chain payment landing on an
address we've already recycled.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from bot.database.main import Database
from bot.database.models.main import CryptoAddress, Order
from bot.payments.crypto_addresses import release_address

logger = logging.getLogger(__name__)

DEFAULT_TTL_HOURS = 24
RECLAIM_INTERVAL_SECONDS = 3600  # hourly

# Order states for which a held address is safe to reclaim.
_RECLAIMABLE_STATES = ("expired", "cancelled")


def reclaim_expired_addresses(ttl_hours: int = DEFAULT_TTL_HOURS) -> tuple[int, list[str]]:
    """Release addresses held by expired/cancelled orders past the TTL.

    Args:
        ttl_hours: Grace period after the address was claimed before it can be
                   reclaimed.

    Returns:
        Tuple of (count released, list of released address strings).
    """
    cutoff = datetime.now(UTC) - timedelta(hours=ttl_hours)
    reclaimed: list[str] = []

    with Database().session() as session:
        candidates = (
            session.query(CryptoAddress)
            .join(Order, CryptoAddress.order_id == Order.id)
            .filter(
                CryptoAddress.is_used.is_(True),
                CryptoAddress.used_at.isnot(None),
                CryptoAddress.used_at < cutoff,
                Order.order_status.in_(_RECLAIMABLE_STATES),
            )
            .all()
        )

        for addr in candidates:
            if release_address(addr.coin, addr.address, session=session):
                reclaimed.append(addr.address)

        session.commit()

    if reclaimed:
        logger.info(
            "Reclaimed %d expired/cancelled crypto address(es): %s",
            len(reclaimed),
            ", ".join(reclaimed),
        )
    return len(reclaimed), reclaimed


async def run_address_reclaimer(ttl_hours: int = DEFAULT_TTL_HOURS, interval: int = RECLAIM_INTERVAL_SECONDS):
    """Background loop: reclaim stale addresses every *interval* seconds."""
    logger.info(
        "Address reclaimer started (ttl=%dh, interval=%ds)",
        ttl_hours,
        interval,
    )
    while True:
        try:
            reclaim_expired_addresses(ttl_hours)
        except Exception:
            logger.exception("Address reclaimer iteration failed")
        await asyncio.sleep(interval)


def start_address_reclaimer(ttl_hours: int = DEFAULT_TTL_HOURS, interval: int = RECLAIM_INTERVAL_SECONDS):
    """Schedule the address reclaimer as a background task."""
    from bot.utils.background import track_task

    track_task(asyncio.create_task(run_address_reclaimer(ttl_hours, interval)))
    logger.info("Address reclaimer task scheduled")
