"""
Comprehensive unit tests for blockchain payment verifiers.

Tests cover TxResult, get_verifier, and all 4 verifiers (BTC, LTC, SOL, USDT-SOL)
with mocked HTTP responses.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock

from bot.payments.chain_verify import TxResult, get_verifier, VERIFIERS
from bot.payments.verifiers.btc import BTCVerifier
from bot.payments.verifiers.ltc import LTCVerifier
from bot.payments.verifiers.sol import SOLVerifier
from bot.payments.verifiers.usdt_sol import USDTSolVerifier, USDT_MINT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data=None, text_data=None, status_code=200, raise_error=False):
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    if raise_error:
        resp.raise_for_status.side_effect = Exception("HTTP error")
    else:
        resp.raise_for_status = MagicMock()
    if json_data is not None:
        resp.json.return_value = json_data
    if text_data is not None:
        resp.text = text_data
    return resp


def _make_async_client(**kwargs):
    """Create a mock httpx.AsyncClient usable as async context manager."""
    client = AsyncMock()
    for key, value in kwargs.items():
        setattr(client, key, value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, client


# ---------------------------------------------------------------------------
# 1. TxResult dataclass defaults
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestTxResult:

    def test_defaults_found_false(self):
        result = TxResult(found=False)
        assert result.found is False
        assert result.tx_hash is None
        assert result.amount is None
        assert result.confirmations is None
        assert result.from_address is None
        assert result.block_height is None
        assert result.timestamp is None

    def test_defaults_found_true_with_values(self):
        result = TxResult(
            found=True,
            tx_hash="abc123",
            amount=Decimal("0.5"),
            confirmations=3,
            from_address="sender_addr",
            block_height=800000,
            timestamp=1700000000,
        )
        assert result.found is True
        assert result.tx_hash == "abc123"
        assert result.amount == Decimal("0.5")
        assert result.confirmations == 3
        assert result.from_address == "sender_addr"
        assert result.block_height == 800000
        assert result.timestamp == 1700000000


# ---------------------------------------------------------------------------
# 2. get_verifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestGetVerifier:

    def test_valid_coins(self):
        for coin in ("btc", "ltc", "sol", "usdt_sol"):
            verifier = get_verifier(coin)
            assert verifier is not None

    def test_btc_returns_btc_verifier(self):
        assert isinstance(get_verifier("btc"), BTCVerifier)

    def test_ltc_returns_ltc_verifier(self):
        assert isinstance(get_verifier("ltc"), LTCVerifier)

    def test_sol_returns_sol_verifier(self):
        assert isinstance(get_verifier("sol"), SOLVerifier)

    def test_usdt_sol_returns_usdt_verifier(self):
        assert isinstance(get_verifier("usdt_sol"), USDTSolVerifier)

    def test_unknown_coin_raises(self):
        with pytest.raises(ValueError, match="No verifier for coin"):
            get_verifier("doge")

    def test_verifiers_dict_has_four_entries(self):
        assert len(VERIFIERS) == 4


# ---------------------------------------------------------------------------
# 3-7. BTC Verifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestBTCVerifier:

    ADDR = "bc1qexampleaddress"

    def _btc_tx(self, value_sat, confirmed=True, block_height=800000, block_time=1700000000):
        """Build a realistic Blockstream-style tx dict."""
        return {
            "txid": "txhash_abc123",
            "vin": [
                {
                    "prevout": {
                        "scriptpubkey_address": "bc1qsenderaddr",
                    }
                }
            ],
            "vout": [
                {
                    "scriptpubkey_address": self.ADDR,
                    "value": value_sat,
                },
                {
                    "scriptpubkey_address": "bc1qchangeaddr",
                    "value": 5000,
                },
            ],
            "status": {
                "confirmed": confirmed,
                "block_height": block_height,
                "block_time": block_time,
            },
        }

    @pytest.mark.asyncio
    async def test_successful_payment(self):
        """BTC: finds a matching payment with correct amount and confirmations."""
        tx = self._btc_tx(value_sat=50000000)  # 0.5 BTC
        txs_resp = _mock_response(json_data=[tx])
        tip_resp = _mock_response(text_data="800005")

        async def mock_get(url, **kwargs):
            if "/txs" in url:
                return txs_resp
            if "tip/height" in url:
                return tip_resp
            raise AssertionError(f"Unexpected GET: {url}")

        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=mock_get)

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", return_value=cm):
            verifier = BTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.5"))

        assert result.found is True
        assert result.tx_hash == "txhash_abc123"
        assert result.amount == Decimal("0.5")
        # tip=800005, block=800000 => confirmations = 800005 - 800000 + 1 = 6
        assert result.confirmations == 6
        assert result.from_address == "bc1qsenderaddr"
        assert result.block_height == 800000
        assert result.timestamp == 1700000000

    @pytest.mark.asyncio
    async def test_no_matching_tx(self):
        """BTC: no transactions at address returns not found."""
        txs_resp = _mock_response(json_data=[])

        cm, client = _make_async_client()
        client.get = AsyncMock(return_value=txs_resp)

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", return_value=cm):
            verifier = BTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.1"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_underpayment(self):
        """BTC: amount below expected returns not found."""
        tx = self._btc_tx(value_sat=1000000)  # 0.01 BTC
        txs_resp = _mock_response(json_data=[tx])
        tip_resp = _mock_response(text_data="800005")

        async def mock_get(url, **kwargs):
            if "/txs" in url:
                return txs_resp
            if "tip/height" in url:
                return tip_resp
            raise AssertionError(f"Unexpected GET: {url}")

        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=mock_get)

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", return_value=cm):
            verifier = BTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.5"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_fallback_to_mempool(self):
        """BTC: when primary (blockstream) fails, falls back to mempool.space."""
        tx = self._btc_tx(value_sat=10000000)  # 0.1 BTC
        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "blockstream.info" in url:
                raise Exception("Blockstream down")
            if "/txs" in url:
                return _mock_response(json_data=[tx])
            if "tip/height" in url:
                return _mock_response(text_data="800010")
            raise AssertionError(f"Unexpected GET: {url}")

        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=mock_get)

        # The verifier creates a new AsyncClient for each base_url attempt,
        # so we need the constructor to return a new CM each time.
        cm2, client2 = _make_async_client()
        client2.get = AsyncMock(side_effect=mock_get)

        call_idx = {"n": 0}
        cms = [cm, cm2]

        def client_factory(**kwargs):
            idx = call_idx["n"]
            call_idx["n"] += 1
            return cms[idx % len(cms)]

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", side_effect=client_factory):
            verifier = BTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.1"))

        assert result.found is True
        assert result.amount == Decimal("0.1")

    @pytest.mark.asyncio
    async def test_unconfirmed_tx(self):
        """BTC: unconfirmed tx gets confirmations=0."""
        tx = self._btc_tx(value_sat=50000000, confirmed=False, block_height=None, block_time=None)
        tx["status"] = {"confirmed": False}
        txs_resp = _mock_response(json_data=[tx])
        tip_resp = _mock_response(text_data="800005")

        async def mock_get(url, **kwargs):
            if "/txs" in url:
                return txs_resp
            if "tip/height" in url:
                return tip_resp
            raise AssertionError(f"Unexpected GET: {url}")

        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=mock_get)

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", return_value=cm):
            verifier = BTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.5"))

        assert result.found is True
        assert result.confirmations == 0

    def test_required_confirmations(self):
        assert BTCVerifier().required_confirmations() == 2

    def test_coin_name(self):
        assert BTCVerifier().coin_name() == "BTC"


# ---------------------------------------------------------------------------
# 8-10. LTC Verifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestLTCVerifier:

    ADDR = "ltc1qexampleaddress"

    def _blockcypher_response(self, txrefs=None, unconfirmed_txrefs=None):
        data = {
            "address": self.ADDR,
            "txrefs": txrefs or [],
            "unconfirmed_txrefs": unconfirmed_txrefs or [],
        }
        return _mock_response(json_data=data)

    @pytest.mark.asyncio
    async def test_successful_detection(self):
        """LTC: finds a matching payment from txrefs."""
        txrefs = [
            {
                "tx_hash": "ltc_txhash_1",
                "value": 50000000,  # 0.5 LTC
                "confirmations": 10,
                "tx_input_n": -1,
                "tx_output_n": 0,
                "block_height": 2500000,
            }
        ]
        resp = self._blockcypher_response(txrefs=txrefs)

        cm, client = _make_async_client()
        client.get = AsyncMock(return_value=resp)

        with patch("bot.payments.verifiers.ltc.httpx.AsyncClient", return_value=cm):
            verifier = LTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.5"))

        assert result.found is True
        assert result.tx_hash == "ltc_txhash_1"
        assert result.amount == Decimal("0.5")
        assert result.confirmations == 10
        assert result.block_height == 2500000
        assert result.from_address is None  # not available in txrefs

    @pytest.mark.asyncio
    async def test_no_txrefs(self):
        """LTC: no txrefs returns not found."""
        resp = self._blockcypher_response()

        cm, client = _make_async_client()
        client.get = AsyncMock(return_value=resp)

        with patch("bot.payments.verifiers.ltc.httpx.AsyncClient", return_value=cm):
            verifier = LTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.1"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_skip_input_txref(self):
        """LTC: txref with tx_input_n >= 0 (spend) is skipped."""
        txrefs = [
            {
                "tx_hash": "ltc_spend",
                "value": 50000000,
                "confirmations": 5,
                "tx_input_n": 0,
                "tx_output_n": -1,
                "block_height": 2500000,
            }
        ]
        resp = self._blockcypher_response(txrefs=txrefs)

        cm, client = _make_async_client()
        client.get = AsyncMock(return_value=resp)

        with patch("bot.payments.verifiers.ltc.httpx.AsyncClient", return_value=cm):
            verifier = LTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("0.1"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_unconfirmed_txrefs(self):
        """LTC: finds payment in unconfirmed_txrefs."""
        unconfirmed = [
            {
                "tx_hash": "ltc_mempool_tx",
                "value": 100000000,  # 1 LTC
                "confirmations": 0,
                "tx_input_n": -1,
                "tx_output_n": 0,
            }
        ]
        resp = self._blockcypher_response(unconfirmed_txrefs=unconfirmed)

        cm, client = _make_async_client()
        client.get = AsyncMock(return_value=resp)

        with patch("bot.payments.verifiers.ltc.httpx.AsyncClient", return_value=cm):
            verifier = LTCVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("1.0"))

        assert result.found is True
        assert result.confirmations == 0

    def test_required_confirmations(self):
        assert LTCVerifier().required_confirmations() == 3

    def test_coin_name(self):
        assert LTCVerifier().coin_name() == "LTC"


# ---------------------------------------------------------------------------
# 11-13. SOL Verifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestSOLVerifier:

    ADDR = "SoLAddressExample1111111111111111111111"
    SENDER = "SoLSenderExample22222222222222222222222"

    def _sigs_response(self, signatures):
        return _mock_response(json_data={"jsonrpc": "2.0", "result": signatures})

    def _tx_response(self, result_data):
        return _mock_response(json_data={"jsonrpc": "2.0", "result": result_data})

    @pytest.mark.asyncio
    async def test_successful_finalized_payment(self):
        """SOL: finds a finalized payment with correct amount."""
        sigs = [{"signature": "sig_abc123", "err": None}]
        tx_result = {
            "slot": 250000000,
            "blockTime": 1700000000,
            "meta": {
                "err": None,
                "preBalances": [5000000000, 1000000000],
                "postBalances": [3500000000, 2500000000],
            },
            "transaction": {
                "message": {
                    "accountKeys": [
                        {"pubkey": self.SENDER},
                        {"pubkey": self.ADDR},
                    ]
                }
            },
        }

        sigs_resp = self._sigs_response(sigs)
        tx_resp = self._tx_response(tx_result)

        async def mock_post(url, **kwargs):
            payload = kwargs.get("json", {})
            method = payload.get("method", "")
            if method == "getSignaturesForAddress":
                return sigs_resp
            if method == "getTransaction":
                return tx_resp
            raise AssertionError(f"Unexpected RPC method: {method}")

        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=mock_post)

        with patch("bot.payments.verifiers.sol.httpx.AsyncClient", return_value=cm):
            verifier = SOLVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("1.5"))

        assert result.found is True
        assert result.tx_hash == "sig_abc123"
        # diff = 2500000000 - 1000000000 = 1500000000 lamports = 1.5 SOL
        assert result.amount == Decimal("1.5")
        assert result.confirmations == 1
        assert result.from_address == self.SENDER
        assert result.block_height == 250000000
        assert result.timestamp == 1700000000

    @pytest.mark.asyncio
    async def test_skip_failed_transactions(self):
        """SOL: transactions with err != None are skipped."""
        sigs = [
            {"signature": "sig_failed", "err": {"InstructionError": [0, "Custom"]}},
        ]
        sigs_resp = self._sigs_response(sigs)

        cm, client = _make_async_client()
        client.post = AsyncMock(return_value=sigs_resp)

        with patch("bot.payments.verifiers.sol.httpx.AsyncClient", return_value=cm):
            verifier = SOLVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("1.0"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_no_signatures(self):
        """SOL: no signatures returns not found."""
        sigs_resp = self._sigs_response([])

        cm, client = _make_async_client()
        client.post = AsyncMock(return_value=sigs_resp)

        with patch("bot.payments.verifiers.sol.httpx.AsyncClient", return_value=cm):
            verifier = SOLVerifier()
            result = await verifier.check_payment(self.ADDR, Decimal("1.0"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_underpayment_sol(self):
        """SOL: amount below expected returns not found (via None from _check_transaction)."""
        sigs = [{"signature": "sig_small", "err": None}]
        tx_result = {
            "slot": 250000000,
            "blockTime": 1700000000,
            "meta": {
                "err": None,
                "preBalances": [5000000000, 1000000000],
                "postBalances": [4900000000, 1100000000],
            },
            "transaction": {
                "message": {
                    "accountKeys": [
                        {"pubkey": self.SENDER},
                        {"pubkey": self.ADDR},
                    ]
                }
            },
        }

        sigs_resp = self._sigs_response(sigs)
        tx_resp = self._tx_response(tx_result)

        async def mock_post(url, **kwargs):
            payload = kwargs.get("json", {})
            method = payload.get("method", "")
            if method == "getSignaturesForAddress":
                return sigs_resp
            if method == "getTransaction":
                return tx_resp
            raise AssertionError(f"Unexpected RPC method: {method}")

        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=mock_post)

        with patch("bot.payments.verifiers.sol.httpx.AsyncClient", return_value=cm):
            verifier = SOLVerifier()
            # diff = 100000000 lamports = 0.1 SOL; expecting 1.0
            result = await verifier.check_payment(self.ADDR, Decimal("1.0"))

        assert result.found is False

    def test_required_confirmations(self):
        assert SOLVerifier().required_confirmations() == 1

    def test_coin_name(self):
        assert SOLVerifier().coin_name() == "SOL"


# ---------------------------------------------------------------------------
# 14-16. USDT (Solana) Verifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestUSDTSolVerifier:

    OWNER = "UsdtOwnerAddr1111111111111111111111111"
    TOKEN_ACCOUNT = "TokenAcct222222222222222222222222222222"
    SENDER = "UsdtSenderAddr333333333333333333333333"

    def _token_accounts_response(self, accounts):
        value = [{"pubkey": acc} for acc in accounts]
        return _mock_response(json_data={
            "jsonrpc": "2.0",
            "result": {"value": value},
        })

    def _empty_token_accounts_response(self):
        return _mock_response(json_data={
            "jsonrpc": "2.0",
            "result": {"value": []},
        })

    def _sigs_response(self, signatures):
        return _mock_response(json_data={"jsonrpc": "2.0", "result": signatures})

    def _usdt_tx_response(self, pre_amount_raw, post_amount_raw,
                          sender_pre_raw="100000000", sender_post_raw="90000000",
                          slot=260000000, block_time=1700100000):
        return _mock_response(json_data={
            "jsonrpc": "2.0",
            "result": {
                "slot": slot,
                "blockTime": block_time,
                "meta": {
                    "err": None,
                    "preTokenBalances": [
                        {
                            "accountIndex": 1,
                            "mint": USDT_MINT,
                            "owner": self.OWNER,
                            "uiTokenAmount": {"amount": pre_amount_raw},
                        },
                        {
                            "accountIndex": 0,
                            "mint": USDT_MINT,
                            "owner": self.SENDER,
                            "uiTokenAmount": {"amount": sender_pre_raw},
                        },
                    ],
                    "postTokenBalances": [
                        {
                            "accountIndex": 1,
                            "mint": USDT_MINT,
                            "owner": self.OWNER,
                            "uiTokenAmount": {"amount": post_amount_raw},
                        },
                        {
                            "accountIndex": 0,
                            "mint": USDT_MINT,
                            "owner": self.SENDER,
                            "uiTokenAmount": {"amount": sender_post_raw},
                        },
                    ],
                },
                "transaction": {
                    "message": {
                        "accountKeys": [
                            {"pubkey": self.SENDER},
                            {"pubkey": self.TOKEN_ACCOUNT},
                        ]
                    }
                },
            },
        })

    @pytest.mark.asyncio
    async def test_successful_usdt_detection(self):
        """USDT: detects a 10 USDT incoming SPL token transfer."""
        token_accts_resp = self._token_accounts_response([self.TOKEN_ACCOUNT])
        sigs_resp = self._sigs_response([{"signature": "usdt_sig_1", "err": None}])
        # 10 USDT = 10_000_000 raw (6 decimals)
        tx_resp = self._usdt_tx_response(
            pre_amount_raw="0",
            post_amount_raw="10000000",
        )

        async def mock_post(url, **kwargs):
            payload = kwargs.get("json", {})
            method = payload.get("method", "")
            if method == "getTokenAccountsByOwner":
                return token_accts_resp
            if method == "getSignaturesForAddress":
                return sigs_resp
            if method == "getTransaction":
                return tx_resp
            raise AssertionError(f"Unexpected RPC method: {method}")

        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=mock_post)

        with patch("bot.payments.verifiers.usdt_sol.httpx.AsyncClient", return_value=cm):
            verifier = USDTSolVerifier()
            result = await verifier.check_payment(self.OWNER, Decimal("10.0"))

        assert result.found is True
        assert result.tx_hash == "usdt_sig_1"
        assert result.amount == Decimal("10")
        assert result.confirmations == 1
        assert result.from_address == self.SENDER
        assert result.block_height == 260000000
        assert result.timestamp == 1700100000

    @pytest.mark.asyncio
    async def test_no_token_accounts(self):
        """USDT: no token accounts for owner returns not found."""
        empty_resp = self._empty_token_accounts_response()

        cm, client = _make_async_client()
        client.post = AsyncMock(return_value=empty_resp)

        with patch("bot.payments.verifiers.usdt_sol.httpx.AsyncClient", return_value=cm):
            verifier = USDTSolVerifier()
            result = await verifier.check_payment(self.OWNER, Decimal("5.0"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_underpayment_usdt(self):
        """USDT: amount below expected returns not found."""
        token_accts_resp = self._token_accounts_response([self.TOKEN_ACCOUNT])
        sigs_resp = self._sigs_response([{"signature": "usdt_sig_small", "err": None}])
        # 1 USDT received, expecting 10
        tx_resp = self._usdt_tx_response(
            pre_amount_raw="0",
            post_amount_raw="1000000",
        )

        async def mock_post(url, **kwargs):
            payload = kwargs.get("json", {})
            method = payload.get("method", "")
            if method == "getTokenAccountsByOwner":
                return token_accts_resp
            if method == "getSignaturesForAddress":
                return sigs_resp
            if method == "getTransaction":
                return tx_resp
            raise AssertionError(f"Unexpected RPC method: {method}")

        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=mock_post)

        with patch("bot.payments.verifiers.usdt_sol.httpx.AsyncClient", return_value=cm):
            verifier = USDTSolVerifier()
            result = await verifier.check_payment(self.OWNER, Decimal("10.0"))

        assert result.found is False

    def test_required_confirmations(self):
        assert USDTSolVerifier().required_confirmations() == 1

    def test_coin_name(self):
        assert USDTSolVerifier().coin_name() == "USDT (SOL)"


# ---------------------------------------------------------------------------
# 17. Network errors — all verifiers return TxResult(found=False)
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.payments
class TestNetworkErrors:

    @pytest.mark.asyncio
    async def test_btc_network_error(self):
        """BTC: network failure on all APIs returns not found."""
        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=Exception("Connection refused"))

        # Both primary and fallback will fail, need 2 CMs
        cm2, client2 = _make_async_client()
        client2.get = AsyncMock(side_effect=Exception("Connection refused"))

        call_idx = {"n": 0}
        cms = [cm, cm2]

        def client_factory(**kwargs):
            idx = call_idx["n"]
            call_idx["n"] += 1
            return cms[idx % len(cms)]

        with patch("bot.payments.verifiers.btc.httpx.AsyncClient", side_effect=client_factory):
            verifier = BTCVerifier()
            result = await verifier.check_payment("bc1qaddr", Decimal("0.1"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_ltc_network_error(self):
        """LTC: network failure returns not found."""
        cm, client = _make_async_client()
        client.get = AsyncMock(side_effect=Exception("Timeout"))

        with patch("bot.payments.verifiers.ltc.httpx.AsyncClient", return_value=cm):
            verifier = LTCVerifier()
            result = await verifier.check_payment("ltc1qaddr", Decimal("0.1"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_sol_network_error(self):
        """SOL: network failure returns not found."""
        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=Exception("DNS resolution failed"))

        with patch("bot.payments.verifiers.sol.httpx.AsyncClient", return_value=cm):
            verifier = SOLVerifier()
            result = await verifier.check_payment("SoLAddr", Decimal("1.0"))

        assert result.found is False

    @pytest.mark.asyncio
    async def test_usdt_network_error(self):
        """USDT: network failure returns not found."""
        cm, client = _make_async_client()
        client.post = AsyncMock(side_effect=Exception("SSL error"))

        with patch("bot.payments.verifiers.usdt_sol.httpx.AsyncClient", return_value=cm):
            verifier = USDTSolVerifier()
            result = await verifier.check_payment("UsdtOwner", Decimal("5.0"))

        assert result.found is False
