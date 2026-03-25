"""Live crypto price feed via CoinGecko (Card 18).

Converts the shop's configured currency (default THB) to crypto amounts at checkout.
CoinGecko supports THB natively — no USD intermediary needed for BTC/LTC/SOL.
USDT is special: since it's pegged to USD, we first convert THB→USD.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Tuple

import httpx

from bot.config.env import EnvKeys

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

COIN_IDS = {
    'btc': 'bitcoin',
    'ltc': 'litecoin',
    'sol': 'solana',
    'usdt_sol': None,  # Special case — needs THB->USD conversion via tether
}

# In-memory price cache: {cache_key: (price, cached_at)}
_price_cache: dict[str, tuple[Decimal, datetime]] = {}
CACHE_TTL = timedelta(minutes=2)


async def get_crypto_amount(coin: str, fiat_amount: Decimal) -> Tuple[Decimal, Decimal]:
    """Convert shop currency amount to crypto amount using live price.

    Returns (crypto_amount, exchange_rate).
    Example: get_crypto_amount('btc', Decimal('1350')) → (Decimal('0.00055102'), Decimal('2450000'))
    """
    shop_currency = EnvKeys.PAY_CURRENCY.lower()  # 'thb'

    if coin == 'usdt_sol':
        # USDT pegged to USD — convert THB→USD
        if shop_currency == 'usd':
            return fiat_amount, Decimal('1')
        usd_in_fiat = await _get_price('tether', shop_currency)  # e.g., 34.5 THB per USDT
        usdt_amount = (fiat_amount / usd_in_fiat).quantize(Decimal('0.01'))
        return usdt_amount, usd_in_fiat

    coin_id = COIN_IDS.get(coin)
    if not coin_id:
        raise ValueError(f"Unknown coin: {coin}")

    price_in_fiat = await _get_price(coin_id, shop_currency)
    if price_in_fiat <= 0:
        raise ValueError(f"Invalid price for {coin}: {price_in_fiat}")
    crypto_amount = fiat_amount / price_in_fiat

    # Round per coin precision
    if coin in ('btc', 'ltc'):
        crypto_amount = crypto_amount.quantize(Decimal('0.00000001'))  # 8 decimals
    elif coin == 'sol':
        crypto_amount = crypto_amount.quantize(Decimal('0.000000001'))  # 9 decimals

    return crypto_amount, price_in_fiat


async def _get_price(coin_id: str, fiat_currency: str) -> Decimal:
    """Fetch current price with 2-minute cache."""
    cache_key = f"{coin_id}_{fiat_currency}"
    if cache_key in _price_cache:
        price, cached_at = _price_cache[cache_key]
        if datetime.now(timezone.utc) - cached_at < CACHE_TTL:
            return price

    headers = {}
    api_key = EnvKeys.COINGECKO_API_KEY
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(COINGECKO_URL, params={
            "ids": coin_id,
            "vs_currencies": fiat_currency,
        }, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        price = Decimal(str(data[coin_id][fiat_currency]))

    _price_cache[cache_key] = (price, datetime.now(timezone.utc))
    logger.debug("Price update: %s = %s %s", coin_id, price, fiat_currency)
    return price


def clear_price_cache():
    """Clear the price cache (for testing)."""
    _price_cache.clear()
