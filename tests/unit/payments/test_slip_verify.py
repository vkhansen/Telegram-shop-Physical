"""Tests for Thai slip verification services (SlipOK, EasySlip, RDCW)."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.payments.slip_verify import (
    SlipProvider,
    SlipVerifyResult,
    VerifyStatus,
    _verify_slipok,
    _verify_easyslip,
    _verify_rdcw,
    verify_slip,
    _parse_datetime,
)


FAKE_SLIP_IMAGE = b"\x89PNG\r\n\x1a\nfake_slip_bytes"


def _mock_aiohttp_response(status, json_data):
    """Helper to create a mock aiohttp response + session."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data)

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_response),
        __aexit__=AsyncMock(return_value=False),
    ))
    return mock_session


# ---------------------------------------------------------------------------
# _parse_datetime
# ---------------------------------------------------------------------------
class TestParseDatetime:
    def test_iso_with_tz(self):
        dt = _parse_datetime("2026-03-22T14:30:00+07:00")
        assert dt is not None
        assert dt.hour == 14

    def test_iso_format(self):
        dt = _parse_datetime("2026-03-22T14:30:00")
        assert dt is not None
        assert dt.hour == 14

    def test_date_only(self):
        dt = _parse_datetime("2026-03-22")
        assert dt is not None
        assert dt.day == 22

    def test_compact_format(self):
        dt = _parse_datetime("20260322143000")
        assert dt is not None

    def test_none_input(self):
        assert _parse_datetime(None) is None

    def test_bad_format(self):
        assert _parse_datetime("not-a-date") is None


# ---------------------------------------------------------------------------
# SlipOK verification
# ---------------------------------------------------------------------------
class TestVerifySlipOK:
    @pytest.mark.asyncio
    async def test_slipok_verified(self):
        mock_session = _mock_aiohttp_response(200, {
            "success": True,
            "data": {
                "transRef": "SLIPOK20260322001",
                "amount": 450.00,
                "date": "2026-03-22",
                "sender": {
                    "bank": {"short": "KBANK"},
                    "account": {"name": {"th": "สมชาย", "en": "Somchai"}},
                },
                "receiver": {
                    "bank": {"short": "SCB"},
                    "account": {"name": {"th": "ร้านอาหาร", "en": "Restaurant"}},
                },
            },
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_slipok(FAKE_SLIP_IMAGE, "api_key", "branch_123")

        assert result.status == VerifyStatus.VERIFIED
        assert result.provider == SlipProvider.SLIPOK
        assert result.transaction_id == "SLIPOK20260322001"
        assert result.amount == Decimal("450.00")
        assert result.sender_name == "Somchai"
        assert result.sender_bank == "KBANK"
        assert result.receiver_bank == "SCB"

    @pytest.mark.asyncio
    async def test_slipok_quota_exceeded(self):
        mock_session = _mock_aiohttp_response(403, {
            "success": False,
            "code": 1007,
            "message": "Quota exceeded",
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_slipok(FAKE_SLIP_IMAGE, "key", "branch")

        assert result.status == VerifyStatus.QUOTA_EXCEEDED

    @pytest.mark.asyncio
    async def test_slipok_not_found(self):
        mock_session = _mock_aiohttp_response(404, {
            "success": False,
            "message": "Transaction not found",
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_slipok(FAKE_SLIP_IMAGE, "key", "branch")

        assert result.status == VerifyStatus.SLIP_NOT_FOUND


# ---------------------------------------------------------------------------
# EasySlip verification
# ---------------------------------------------------------------------------
class TestVerifyEasySlip:
    @pytest.mark.asyncio
    async def test_easyslip_verified(self):
        mock_session = _mock_aiohttp_response(200, {
            "success": True,
            "data": {
                "isDuplicate": False,
                "isAmountMatched": True,
                "amountInSlip": 300,
                "amountInOrder": 300,
                "rawSlip": {
                    "transRef": "ES20260322002",
                    "date": "2026-03-22T12:00:00+07:00",
                    "amount": {"amount": 300, "local": {"amount": 300, "currency": "THB"}},
                    "sender": {
                        "bank": {"short": "BBL"},
                        "account": {"name": {"en": "John Doe"}},
                    },
                    "receiver": {
                        "bank": {"short": "KBANK"},
                        "account": {"name": {"en": "My Shop"}},
                    },
                },
            },
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_easyslip(FAKE_SLIP_IMAGE, "bearer_key", "", Decimal("300"))

        assert result.status == VerifyStatus.VERIFIED
        assert result.provider == SlipProvider.EASYSLIP
        assert result.amount == Decimal("300")
        assert result.is_duplicate is False
        assert result.sender_name == "John Doe"

    @pytest.mark.asyncio
    async def test_easyslip_duplicate(self):
        mock_session = _mock_aiohttp_response(200, {
            "success": True,
            "data": {
                "isDuplicate": True,
                "rawSlip": {
                    "transRef": "ES_DUP001",
                },
            },
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_easyslip(FAKE_SLIP_IMAGE, "key")

        assert result.status == VerifyStatus.DUPLICATE
        assert result.transaction_id == "ES_DUP001"

    @pytest.mark.asyncio
    async def test_easyslip_amount_mismatch(self):
        mock_session = _mock_aiohttp_response(200, {
            "success": True,
            "data": {
                "isDuplicate": False,
                "isAmountMatched": False,
                "amountInSlip": 500,
                "amountInOrder": 300,
                "rawSlip": {
                    "transRef": "ES003",
                    "amount": {"amount": 500},
                    "sender": {"bank": {}, "account": {"name": {}}},
                    "receiver": {"bank": {}, "account": {"name": {}}},
                },
            },
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_easyslip(FAKE_SLIP_IMAGE, "key", "", Decimal("300"))

        assert result.status == VerifyStatus.AMOUNT_MISMATCH

    @pytest.mark.asyncio
    async def test_easyslip_not_found(self):
        mock_session = _mock_aiohttp_response(404, {
            "success": False,
            "error": {"code": "SLIP_NOT_FOUND", "message": "Slip not found"},
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_easyslip(FAKE_SLIP_IMAGE, "key")

        assert result.status == VerifyStatus.SLIP_NOT_FOUND


# ---------------------------------------------------------------------------
# RDCW verification
# ---------------------------------------------------------------------------
class TestVerifyRDCW:
    @pytest.mark.asyncio
    async def test_rdcw_verified(self):
        mock_session = _mock_aiohttp_response(200, {
            "success": True,
            "data": {
                "data": {
                    "amount": 45000,  # satang (= 450.00 THB)
                    "transDate": "20260322",
                    "transTime": "14:30:00",
                    "sendingBank": "004",
                    "sender": {"name": "Somchai"},
                    "receiver": {"name": "Restaurant"},
                },
            },
            "quota": {"limit": 500, "usage": 42},
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_rdcw(FAKE_SLIP_IMAGE, "client_id", "client_secret")

        assert result.status == VerifyStatus.VERIFIED
        assert result.provider == SlipProvider.RDCW
        assert result.amount == Decimal("450.00")
        assert result.sender_name == "Somchai"
        assert result.receiver_name == "Restaurant"

    @pytest.mark.asyncio
    async def test_rdcw_quota_exceeded(self):
        mock_session = _mock_aiohttp_response(403, {
            "success": False,
            "code": 1007,
            "message": "Usage exceeded",
        })

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _verify_rdcw(FAKE_SLIP_IMAGE, "id", "secret")

        assert result.status == VerifyStatus.QUOTA_EXCEEDED


# ---------------------------------------------------------------------------
# verify_slip (unified)
# ---------------------------------------------------------------------------
class TestVerifySlip:
    @pytest.mark.asyncio
    async def test_no_api_configured(self):
        with patch("bot.payments.slip_verify._get_configured_providers", return_value=[]):
            result = await verify_slip(FAKE_SLIP_IMAGE)

        assert result.status == VerifyStatus.NO_API_CONFIGURED

    @pytest.mark.asyncio
    async def test_amount_mismatch_cross_check(self):
        """verify_slip cross-checks amount even if provider said verified."""
        verified_result = SlipVerifyResult(
            status=VerifyStatus.VERIFIED,
            provider=SlipProvider.SLIPOK,
            transaction_id="TXN001",
            amount=Decimal("500.00"),
        )
        mock_verifier = AsyncMock(return_value=verified_result)

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[(SlipProvider.SLIPOK, "k", "b")]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS",
                        {SlipProvider.SLIPOK: mock_verifier}):
            result = await verify_slip(FAKE_SLIP_IMAGE, expected_amount=Decimal("450.00"))

        assert result.status == VerifyStatus.AMOUNT_MISMATCH

    @pytest.mark.asyncio
    async def test_receiver_mismatch_cross_check(self):
        verified_result = SlipVerifyResult(
            status=VerifyStatus.VERIFIED,
            provider=SlipProvider.EASYSLIP,
            transaction_id="TXN002",
            amount=Decimal("450.00"),
            receiver_name="Wrong Person",
        )
        mock_verifier = AsyncMock(return_value=verified_result)

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[(SlipProvider.EASYSLIP, "k", "")]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS",
                        {SlipProvider.EASYSLIP: mock_verifier}):
            result = await verify_slip(
                FAKE_SLIP_IMAGE,
                expected_amount=Decimal("450.00"),
                expected_receiver="Restaurant",
            )

        assert result.status == VerifyStatus.RECIPIENT_MISMATCH

    @pytest.mark.asyncio
    async def test_fallback_on_not_found(self):
        """If first provider returns SLIP_NOT_FOUND, try the next one."""
        not_found = SlipVerifyResult(status=VerifyStatus.SLIP_NOT_FOUND, provider=SlipProvider.SLIPOK)
        verified = SlipVerifyResult(
            status=VerifyStatus.VERIFIED,
            provider=SlipProvider.RDCW,
            transaction_id="RDCW001",
            amount=Decimal("100.00"),
        )

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[
                        (SlipProvider.SLIPOK, "k1", "b1"),
                        (SlipProvider.RDCW, "id", "secret"),
                    ]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS", {
                 SlipProvider.SLIPOK: AsyncMock(return_value=not_found),
                 SlipProvider.RDCW: AsyncMock(return_value=verified),
             }):
            result = await verify_slip(FAKE_SLIP_IMAGE)

        assert result.status == VerifyStatus.VERIFIED
        assert result.provider == SlipProvider.RDCW

    @pytest.mark.asyncio
    async def test_fallback_on_quota_exceeded(self):
        """If first provider quota exceeded, try next."""
        quota_err = SlipVerifyResult(status=VerifyStatus.QUOTA_EXCEEDED, provider=SlipProvider.SLIPOK)
        verified = SlipVerifyResult(
            status=VerifyStatus.VERIFIED,
            provider=SlipProvider.EASYSLIP,
            amount=Decimal("200.00"),
        )

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[
                        (SlipProvider.SLIPOK, "k", "b"),
                        (SlipProvider.EASYSLIP, "k2", ""),
                    ]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS", {
                 SlipProvider.SLIPOK: AsyncMock(return_value=quota_err),
                 SlipProvider.EASYSLIP: AsyncMock(return_value=verified),
             }):
            result = await verify_slip(FAKE_SLIP_IMAGE)

        assert result.status == VerifyStatus.VERIFIED

    @pytest.mark.asyncio
    async def test_duplicate_stops_immediately(self):
        """Duplicate detection is definitive — don't try other providers."""
        duplicate = SlipVerifyResult(
            status=VerifyStatus.DUPLICATE,
            provider=SlipProvider.EASYSLIP,
            transaction_id="DUP001",
        )
        second_mock = AsyncMock()

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[
                        (SlipProvider.EASYSLIP, "k", ""),
                        (SlipProvider.RDCW, "id", "secret"),
                    ]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS", {
                 SlipProvider.EASYSLIP: AsyncMock(return_value=duplicate),
                 SlipProvider.RDCW: second_mock,
             }):
            result = await verify_slip(FAKE_SLIP_IMAGE)

        assert result.status == VerifyStatus.DUPLICATE
        second_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_exact_amount_verified(self):
        verified_result = SlipVerifyResult(
            status=VerifyStatus.VERIFIED,
            provider=SlipProvider.SLIPOK,
            transaction_id="OK001",
            amount=Decimal("250.00"),
        )
        mock_verifier = AsyncMock(return_value=verified_result)

        with patch("bot.payments.slip_verify._get_configured_providers",
                    return_value=[(SlipProvider.SLIPOK, "k", "b")]), \
             patch.dict("bot.payments.slip_verify._PROVIDER_VERIFIERS",
                        {SlipProvider.SLIPOK: mock_verifier}):
            result = await verify_slip(FAKE_SLIP_IMAGE, expected_amount=Decimal("250.00"))

        assert result.status == VerifyStatus.VERIFIED
        assert result.transaction_id == "OK001"
