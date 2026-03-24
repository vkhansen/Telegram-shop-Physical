"""Tests for crypto-related constants (Card 18)."""

import pytest

from bot.utils.constants import (
    PAYMENT_BITCOIN, PAYMENT_LITECOIN, PAYMENT_SOLANA, PAYMENT_USDT_SOL,
    PAYMENT_CASH, PAYMENT_PROMPTPAY,
    COIN_BTC, COIN_LTC, COIN_SOL, COIN_USDT_SOL,
    PAYMENT_METHOD_TO_COIN, CRYPTO_PAYMENT_METHODS,
)


@pytest.mark.unit
class TestCryptoConstants:

    def test_payment_method_strings(self):
        assert PAYMENT_BITCOIN == "bitcoin"
        assert PAYMENT_LITECOIN == "litecoin"
        assert PAYMENT_SOLANA == "solana"
        assert PAYMENT_USDT_SOL == "usdt_sol"
        assert PAYMENT_CASH == "cash"
        assert PAYMENT_PROMPTPAY == "promptpay"

    def test_coin_code_strings(self):
        assert COIN_BTC == "btc"
        assert COIN_LTC == "ltc"
        assert COIN_SOL == "sol"
        assert COIN_USDT_SOL == "usdt_sol"

    def test_payment_method_to_coin_mapping(self):
        assert PAYMENT_METHOD_TO_COIN[PAYMENT_BITCOIN] == COIN_BTC
        assert PAYMENT_METHOD_TO_COIN[PAYMENT_LITECOIN] == COIN_LTC
        assert PAYMENT_METHOD_TO_COIN[PAYMENT_SOLANA] == COIN_SOL
        assert PAYMENT_METHOD_TO_COIN[PAYMENT_USDT_SOL] == COIN_USDT_SOL

    def test_crypto_payment_methods_set(self):
        assert PAYMENT_BITCOIN in CRYPTO_PAYMENT_METHODS
        assert PAYMENT_LITECOIN in CRYPTO_PAYMENT_METHODS
        assert PAYMENT_SOLANA in CRYPTO_PAYMENT_METHODS
        assert PAYMENT_USDT_SOL in CRYPTO_PAYMENT_METHODS
        assert PAYMENT_CASH not in CRYPTO_PAYMENT_METHODS
        assert PAYMENT_PROMPTPAY not in CRYPTO_PAYMENT_METHODS

    def test_all_crypto_methods_have_coin_mapping(self):
        for method in CRYPTO_PAYMENT_METHODS:
            assert method in PAYMENT_METHOD_TO_COIN
