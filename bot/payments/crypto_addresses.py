"""
Multi-coin address pool management module.

Generalises the bitcoin.py pattern (BitcoinAddress + SELECT FOR UPDATE SKIP LOCKED)
to work with any supported cryptocurrency via the CryptoAddress model.
"""

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bot.database.main import Database
from bot.database.models.main import CryptoAddress

logger = logging.getLogger(__name__)

# Mapping of coin identifiers to their address files
COIN_ADDRESS_FILES = {
    'btc': 'crypto_addresses/btc_addresses.txt',
    'ltc': 'crypto_addresses/ltc_addresses.txt',
    'sol': 'crypto_addresses/sol_addresses.txt',
    'usdt_sol': 'crypto_addresses/usdt_sol_addresses.txt',
}

# Lock for thread-safe file operations
_file_lock = threading.Lock()


def _get_address_file(coin: str) -> Path:
    """Return the Path for a coin's address file, or raise ValueError."""
    filename = COIN_ADDRESS_FILES.get(coin)
    if filename is None:
        raise ValueError(f"Unknown coin: {coin!r}. Supported: {list(COIN_ADDRESS_FILES)}")
    return Path(filename)


def load_addresses_for_coin(coin: str) -> int:
    """
    Load addresses from the coin's text file into the crypto_addresses table.

    Skips comment lines (starting with #), blank lines, and addresses that
    already exist in the database for this coin.

    Returns:
        Number of new addresses loaded.
    """
    address_file = _get_address_file(coin)

    if not address_file.exists():
        logger.warning("Address file not found for %s: %s", coin, address_file)
        address_file.parent.mkdir(parents=True, exist_ok=True)
        address_file.touch()
        return 0

    with _file_lock:
        with open(address_file, 'r') as f:
            addresses = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith('#')
            ]

    if not addresses:
        logger.info("No addresses found in file for %s", coin)
        return 0

    loaded_count = 0
    with Database().session() as session:
        for address in addresses:
            existing = (
                session.query(CryptoAddress)
                .filter_by(coin=coin, address=address)
                .first()
            )
            if not existing:
                crypto_addr = CryptoAddress(coin=coin, address=address)
                session.add(crypto_addr)
                loaded_count += 1

        session.commit()

    logger.info("Loaded %d new %s addresses into database", loaded_count, coin)
    return loaded_count


def get_available_address(coin: str, user_id: int = None, order_id: int = None) -> Optional[str]:
    """
    Atomically claim an unused address for the given coin.

    Uses SELECT FOR UPDATE SKIP LOCKED to prevent double assignment
    under concurrent access.

    Args:
        coin: Coin identifier (e.g. 'btc', 'ltc', 'sol', 'usdt_sol').
        user_id: Telegram user ID to associate with the address.
        order_id: Order ID to associate with the address.

    Returns:
        The claimed address string, or None if no addresses are available.
    """
    with Database().session() as session:
        crypto_addr = (
            session.query(CryptoAddress)
            .filter_by(coin=coin, is_used=False)
            .with_for_update(skip_locked=True)
            .first()
        )

        if crypto_addr:
            crypto_addr.is_used = True
            if user_id is not None:
                crypto_addr.used_by = user_id
            if order_id is not None:
                crypto_addr.order_id = order_id
            crypto_addr.used_at = datetime.now(timezone.utc)
            session.commit()
            logger.info(
                "Claimed %s address %s for user=%s order=%s",
                coin, crypto_addr.address, user_id, order_id,
            )
            return crypto_addr.address

    logger.warning("No available %s addresses in pool", coin)
    return None


def mark_address_used(coin: str, address: str, user_id: int, order_id: int,
                      session=None) -> bool:
    """
    Mark a specific address as used in the database and remove it from file.

    Args:
        coin: Coin identifier.
        address: The crypto address string.
        user_id: Telegram user ID.
        order_id: Order ID.
        session: Optional SQLAlchemy session. If provided, the caller is
                 responsible for committing the transaction.

    Returns:
        True if the address was found and marked, False otherwise.
    """
    if session:
        crypto_addr = (
            session.query(CryptoAddress)
            .filter_by(coin=coin, address=address)
            .first()
        )
        if not crypto_addr:
            logger.warning("Address not found in DB: coin=%s address=%s", coin, address)
            return False

        crypto_addr.is_used = True
        crypto_addr.used_by = user_id
        crypto_addr.used_at = datetime.now(timezone.utc)
        crypto_addr.order_id = order_id
        # Don't commit — caller will handle it
    else:
        with Database().session() as db_session:
            crypto_addr = (
                db_session.query(CryptoAddress)
                .filter_by(coin=coin, address=address)
                .first()
            )
            if not crypto_addr:
                logger.warning("Address not found in DB: coin=%s address=%s", coin, address)
                return False

            crypto_addr.is_used = True
            crypto_addr.used_by = user_id
            crypto_addr.used_at = datetime.now(timezone.utc)
            crypto_addr.order_id = order_id
            db_session.commit()

    # Remove from file regardless of session mode
    remove_address_from_file(coin, address)

    logger.info("Marked %s address %s as used (user=%s, order=%s)", coin, address, user_id, order_id)
    return True


def remove_address_from_file(coin: str, address: str) -> None:
    """
    Remove a specific address from the coin's address file.

    Preserves comments and blank lines. No-op if the file does not exist.
    """
    address_file = _get_address_file(coin)

    if not address_file.exists():
        return

    with _file_lock:
        with open(address_file, 'r') as f:
            lines = [line.rstrip('\n') for line in f]

        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            # Keep comments, empty lines, and any line that doesn't match
            if not stripped or stripped.startswith('#') or stripped != address:
                filtered_lines.append(line)

        with open(address_file, 'w') as f:
            for line in filtered_lines:
                f.write(f"{line}\n")


def get_address_stats(coin: str = None) -> dict:
    """
    Return address pool statistics.

    Args:
        coin: If provided, stats for that coin only. If None, aggregate across all coins.

    Returns:
        Dict with keys 'total', 'used', 'available'.
    """
    with Database().session() as session:
        base_query = session.query(CryptoAddress)
        if coin is not None:
            base_query = base_query.filter_by(coin=coin)

        total = base_query.count()
        used = base_query.filter(CryptoAddress.is_used == True).count()
        available = total - used

        return {
            'total': total,
            'used': used,
            'available': available,
        }


def load_all_addresses() -> dict:
    """
    Load addresses for all enabled coins from their respective files.

    Returns:
        Dict mapping coin identifier to the number of new addresses loaded,
        e.g. {'btc': 5, 'ltc': 0, 'sol': 12, 'usdt_sol': 3}.
    """
    results = {}
    for coin in COIN_ADDRESS_FILES:
        try:
            results[coin] = load_addresses_for_coin(coin)
        except Exception:
            logger.exception("Failed to load addresses for %s", coin)
            results[coin] = 0
    return results
