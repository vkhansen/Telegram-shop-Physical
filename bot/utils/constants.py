"""
Application-wide constants and shared tiny helpers to replace magic strings.
"""
import logging

_logger = logging.getLogger(__name__)


def parse_callback_id(data: str, prefix: str) -> int | None:
    """Extract integer ID from callback_data after removing prefix.

    Returns None (instead of crashing) if the value is not a valid integer.
    """
    try:
        return int(data.replace(prefix, ""))
    except (ValueError, TypeError):
        _logger.warning("Invalid callback data: %r (prefix=%r)", data, prefix)
        return None


# Valid delivery types for validation
VALID_DELIVERY_TYPES = frozenset({"door", "dead_drop", "pickup"})

# Payment methods
PAYMENT_BITCOIN = "bitcoin"
PAYMENT_LITECOIN = "litecoin"
PAYMENT_SOLANA = "solana"
PAYMENT_USDT_SOL = "usdt_sol"
PAYMENT_CASH = "cash"
PAYMENT_PROMPTPAY = "promptpay"

# Coin codes (for address pools & verifiers)
COIN_BTC = "btc"
COIN_LTC = "ltc"
COIN_SOL = "sol"
COIN_USDT_SOL = "usdt_sol"

# Maps payment method → coin code (crypto methods only)
PAYMENT_METHOD_TO_COIN = {
    PAYMENT_BITCOIN: COIN_BTC,
    PAYMENT_LITECOIN: COIN_LTC,
    PAYMENT_SOLANA: COIN_SOL,
    PAYMENT_USDT_SOL: COIN_USDT_SOL,
}

CRYPTO_PAYMENT_METHODS = set(PAYMENT_METHOD_TO_COIN.keys())

# Delivery types (Card 3)
DELIVERY_DOOR = "door"
DELIVERY_DEAD_DROP = "dead_drop"
DELIVERY_PICKUP = "pickup"

# Order statuses
STATUS_PENDING = "pending"
STATUS_RESERVED = "reserved"
STATUS_CONFIRMED = "confirmed"
STATUS_PREPARING = "preparing"
STATUS_READY = "ready"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_DELIVERED = "delivered"
STATUS_CANCELLED = "cancelled"
STATUS_EXPIRED = "expired"

# Order status → emoji mapping (shared across admin & user views)
STATUS_EMOJI = {
    "pending": "\u23f3",
    "reserved": "\U0001f512",
    "confirmed": "\u2705",
    "preparing": "\U0001f373",
    "ready": "\U0001f4e6",
    "out_for_delivery": "\U0001f697",
    "delivered": "\u2705",
    "cancelled": "\u274c",
    "canceled": "\u274c",
    "expired": "\u23f0",
}
