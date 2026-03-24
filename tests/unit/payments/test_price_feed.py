"""
Tests for bot.payments.price_feed module — CoinGecko live price feed.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from bot.payments.price_feed import (
    get_crypto_amount,
    _get_price,
    clear_price_cache,
    _price_cache,
    CACHE_TTL,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure price cache is empty before and after each test."""
    clear_price_cache()
    yield
    clear_price_cache()


def _mock_response(json_data, status_code=200):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


def _patch_httpx(json_data, status_code=200):
    """Return a patch context manager that mocks httpx.AsyncClient."""
    mock_resp = _mock_response(json_data, status_code)
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return patch("bot.payments.price_feed.httpx.AsyncClient", return_value=mock_client)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestGetCryptoAmountBTC:
    """BTC conversion with mocked CoinGecko response."""

    async def test_btc_conversion(self):
        with _patch_httpx({"bitcoin": {"thb": 2450000}}), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            mock_env.COINGECKO_API_KEY = ""

            amount, rate = await get_crypto_amount("btc", Decimal("1350"))

        assert rate == Decimal("2450000")
        expected = (Decimal("1350") / Decimal("2450000")).quantize(Decimal("0.00000001"))
        assert amount == expected


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestGetCryptoAmountLTC:
    """LTC conversion with 8-decimal rounding."""

    async def test_ltc_8_decimal_rounding(self):
        with _patch_httpx({"litecoin": {"thb": 3500}}), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            mock_env.COINGECKO_API_KEY = ""

            amount, rate = await get_crypto_amount("ltc", Decimal("700"))

        assert rate == Decimal("3500")
        expected = (Decimal("700") / Decimal("3500")).quantize(Decimal("0.00000001"))
        assert amount == expected
        # Verify exactly 8 decimal places
        assert abs(amount.as_tuple().exponent) == 8


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestGetCryptoAmountSOL:
    """SOL conversion with 9-decimal rounding."""

    async def test_sol_9_decimal_rounding(self):
        with _patch_httpx({"solana": {"thb": 5200}}), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            mock_env.COINGECKO_API_KEY = ""

            amount, rate = await get_crypto_amount("sol", Decimal("1040"))

        assert rate == Decimal("5200")
        expected = (Decimal("1040") / Decimal("5200")).quantize(Decimal("0.000000001"))
        assert amount == expected
        # Verify exactly 9 decimal places
        assert abs(amount.as_tuple().exponent) == 9


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestGetCryptoAmountUSDT:
    """USDT THB->USD conversion via tether price."""

    async def test_usdt_thb_conversion(self):
        with _patch_httpx({"tether": {"thb": Decimal("34.5")}}), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            mock_env.COINGECKO_API_KEY = ""

            amount, rate = await get_crypto_amount("usdt_sol", Decimal("690"))

        assert rate == Decimal("34.5")
        expected = (Decimal("690") / Decimal("34.5")).quantize(Decimal("0.01"))
        assert amount == expected

    async def test_usdt_usd_shop_currency_returns_one_to_one(self):
        """When shop currency is already USD, USDT should be 1:1."""
        with patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "USD"

            amount, rate = await get_crypto_amount("usdt_sol", Decimal("50.00"))

        assert rate == Decimal("1")
        assert amount == Decimal("50.00")


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestGetPriceCaching:
    """_get_price should cache results for CACHE_TTL duration."""

    async def test_second_call_uses_cache(self):
        mock_resp = _mock_response({"bitcoin": {"thb": 2450000}})
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bot.payments.price_feed.httpx.AsyncClient", return_value=mock_client), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.COINGECKO_API_KEY = ""

            price1 = await _get_price("bitcoin", "thb")
            price2 = await _get_price("bitcoin", "thb")

        assert price1 == Decimal("2450000")
        assert price2 == Decimal("2450000")
        # API should only be called once — second call served from cache
        assert mock_client.get.call_count == 1


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestClearPriceCache:
    """clear_price_cache should empty the cache."""

    async def test_clear_cache_forces_new_api_call(self):
        mock_resp = _mock_response({"bitcoin": {"thb": 2450000}})
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("bot.payments.price_feed.httpx.AsyncClient", return_value=mock_client), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.COINGECKO_API_KEY = ""

            await _get_price("bitcoin", "thb")
            assert len(_price_cache) == 1

            clear_price_cache()
            assert len(_price_cache) == 0

            await _get_price("bitcoin", "thb")

        # Two API calls because cache was cleared between them
        assert mock_client.get.call_count == 2


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestUnknownCoin:
    """Unknown coin identifier should raise ValueError."""

    async def test_unknown_coin_raises(self):
        with pytest.raises(ValueError, match="Unknown coin"):
            await get_crypto_amount("doge", Decimal("100"))


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.payments
class TestAPIError:
    """HTTP errors from CoinGecko should propagate."""

    async def test_api_error_propagates(self):
        with _patch_httpx({}, status_code=500), \
             patch("bot.payments.price_feed.EnvKeys") as mock_env:
            mock_env.PAY_CURRENCY = "THB"
            mock_env.COINGECKO_API_KEY = ""

            with pytest.raises(httpx.HTTPStatusError):
                await get_crypto_amount("btc", Decimal("1000"))
