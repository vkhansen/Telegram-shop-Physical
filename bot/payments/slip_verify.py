"""
Thai bank slip verification via third-party verification services.

Supports three providers that verify PromptPay slips across ALL Thai banks
with a single API key:

  1. SlipOK   (slipok.com)           — free tier 100 slips/mo
  2. EasySlip (easyslip.com)         — duplicate detection built-in
  3. RDCW     (slip.rdcw.co.th)      — pay-as-you-go, cheapest at volume

The bot tries each configured provider in order until one succeeds.
"""
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & result types
# ---------------------------------------------------------------------------

class SlipProvider(str, Enum):
    SLIPOK = "slipok"
    EASYSLIP = "easyslip"
    RDCW = "rdcw"


class VerifyStatus(str, Enum):
    VERIFIED = "verified"
    AMOUNT_MISMATCH = "amount_mismatch"
    RECIPIENT_MISMATCH = "recipient_mismatch"
    SLIP_NOT_FOUND = "slip_not_found"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    API_ERROR = "api_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    NO_API_CONFIGURED = "no_api_configured"


@dataclass
class SlipVerifyResult:
    status: VerifyStatus
    provider: Optional[SlipProvider] = None
    transaction_id: Optional[str] = None
    amount: Optional[Decimal] = None
    sender_name: Optional[str] = None
    sender_bank: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_bank: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_duplicate: Optional[bool] = None
    raw_response: Optional[dict] = None
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# SlipOK — https://slipok.com/api-documentation/
# POST https://api.slipok.com/api/line/apikey/{branch_id}
# Auth: x-authorization header
# Input: multipart file upload (field: "files") or JSON {"data": qr_payload}
# Free tier: 100 slips/month
# ---------------------------------------------------------------------------
async def _verify_slipok(
    slip_image: bytes,
    api_key: str,
    branch_id: str,
    expected_amount: Optional[Decimal] = None,
) -> SlipVerifyResult:
    url = f"https://api.slipok.com/api/line/apikey/{branch_id}"

    headers = {
        "x-authorization": api_key,
    }

    form = aiohttp.FormData()
    form.add_field("files", slip_image, filename="slip.jpg", content_type="image/jpeg")
    if expected_amount is not None:
        form.add_field("amount", str(expected_amount))

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()

                if resp.status != 200 or not data.get("success"):
                    code = data.get("code")
                    msg = data.get("message", f"HTTP {resp.status}")

                    if code == 1007:
                        return SlipVerifyResult(
                            status=VerifyStatus.QUOTA_EXCEEDED,
                            provider=SlipProvider.SLIPOK,
                            error_message="SlipOK quota exceeded",
                            raw_response=data,
                        )

                    return SlipVerifyResult(
                        status=VerifyStatus.API_ERROR if resp.status != 404 else VerifyStatus.SLIP_NOT_FOUND,
                        provider=SlipProvider.SLIPOK,
                        error_message=msg,
                        raw_response=data,
                    )

                slip_data = data.get("data", {})

                sender = slip_data.get("sender", {})
                receiver = slip_data.get("receiver", {})
                sender_acct = sender.get("account", {})
                receiver_acct = receiver.get("account", {})

                sender_name_obj = sender_acct.get("name", {})
                receiver_name_obj = receiver_acct.get("name", {})

                return SlipVerifyResult(
                    status=VerifyStatus.VERIFIED,
                    provider=SlipProvider.SLIPOK,
                    transaction_id=slip_data.get("transRef"),
                    amount=Decimal(str(slip_data["amount"])) if slip_data.get("amount") is not None else None,
                    sender_name=sender_name_obj.get("en") or sender_name_obj.get("th"),
                    sender_bank=sender.get("bank", {}).get("short"),
                    receiver_name=receiver_name_obj.get("en") or receiver_name_obj.get("th"),
                    receiver_bank=receiver.get("bank", {}).get("short"),
                    timestamp=_parse_datetime(slip_data.get("date")),
                    raw_response=data,
                )

    except aiohttp.ClientError as e:
        logger.error("SlipOK connection error: %s", e)
        return SlipVerifyResult(
            status=VerifyStatus.API_ERROR,
            provider=SlipProvider.SLIPOK,
            error_message=str(e),
        )


# ---------------------------------------------------------------------------
# EasySlip — https://document.easyslip.com/en/v2/verify/bank/
# POST https://api.easyslip.com/v2/verify/bank
# Auth: Authorization: Bearer {api_key}
# Input: multipart image, base64 JSON, payload JSON, or URL JSON
# Built-in: duplicate detection, amount matching, account matching
# ---------------------------------------------------------------------------
async def _verify_easyslip(
    slip_image: bytes,
    api_key: str,
    _unused: str = "",
    expected_amount: Optional[Decimal] = None,
) -> SlipVerifyResult:
    url = "https://api.easyslip.com/v2/verify/bank"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "base64": base64.b64encode(slip_image).decode("ascii"),
        "checkDuplicate": True,
    }
    if expected_amount is not None:
        payload["matchAmount"] = float(expected_amount)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()

                if resp.status == 403:
                    error_code = data.get("error", {}).get("code", "")
                    if error_code == "QUOTA_EXCEEDED":
                        return SlipVerifyResult(
                            status=VerifyStatus.QUOTA_EXCEEDED,
                            provider=SlipProvider.EASYSLIP,
                            error_message="EasySlip quota exceeded",
                            raw_response=data,
                        )

                if resp.status == 404:
                    return SlipVerifyResult(
                        status=VerifyStatus.SLIP_NOT_FOUND,
                        provider=SlipProvider.EASYSLIP,
                        error_message=data.get("error", {}).get("message", "Slip not found"),
                        raw_response=data,
                    )

                if resp.status != 200 or not data.get("success"):
                    return SlipVerifyResult(
                        status=VerifyStatus.API_ERROR,
                        provider=SlipProvider.EASYSLIP,
                        error_message=data.get("error", {}).get("message", f"HTTP {resp.status}"),
                        raw_response=data,
                    )

                slip_data = data.get("data", {})
                raw_slip = slip_data.get("rawSlip", {})

                # Check duplicate
                if slip_data.get("isDuplicate"):
                    return SlipVerifyResult(
                        status=VerifyStatus.DUPLICATE,
                        provider=SlipProvider.EASYSLIP,
                        transaction_id=raw_slip.get("transRef"),
                        error_message="This slip has already been used",
                        raw_response=data,
                    )

                # Check amount match (EasySlip does this server-side too)
                amount_matched = slip_data.get("isAmountMatched")
                amount_in_slip = slip_data.get("amountInSlip")

                sender = raw_slip.get("sender", {})
                receiver = raw_slip.get("receiver", {})
                sender_acct = sender.get("account", {})
                receiver_acct = receiver.get("account", {})
                sender_name_obj = sender_acct.get("name", {})
                receiver_name_obj = receiver_acct.get("name", {})

                amount_obj = raw_slip.get("amount", {})
                amount_val = amount_obj.get("amount") if isinstance(amount_obj, dict) else amount_in_slip

                result = SlipVerifyResult(
                    status=VerifyStatus.VERIFIED,
                    provider=SlipProvider.EASYSLIP,
                    transaction_id=raw_slip.get("transRef"),
                    amount=Decimal(str(amount_val)) if amount_val is not None else None,
                    sender_name=sender_name_obj.get("en") or sender_name_obj.get("th"),
                    sender_bank=sender.get("bank", {}).get("short"),
                    receiver_name=receiver_name_obj.get("en") or receiver_name_obj.get("th"),
                    receiver_bank=receiver.get("bank", {}).get("short"),
                    timestamp=_parse_datetime(raw_slip.get("date")),
                    is_duplicate=False,
                    raw_response=data,
                )

                # If EasySlip says amount doesn't match, flag it
                if amount_matched is False:
                    result.status = VerifyStatus.AMOUNT_MISMATCH
                    result.error_message = (
                        f"Amount mismatch: slip shows {amount_in_slip} THB, "
                        f"expected {slip_data.get('amountInOrder')} THB"
                    )

                return result

    except aiohttp.ClientError as e:
        logger.error("EasySlip connection error: %s", e)
        return SlipVerifyResult(
            status=VerifyStatus.API_ERROR,
            provider=SlipProvider.EASYSLIP,
            error_message=str(e),
        )


# ---------------------------------------------------------------------------
# RDCW Slip Verify — https://slip.rdcw.co.th/docs
# POST https://suba.rdcw.co.th/v2/inquiry
# Auth: HTTP Basic (clientId:clientSecret)
# Input: multipart file upload (field: "file") or JSON {"payload": qr_string}
# Note: amount returned in satang (÷100 for THB)
# ---------------------------------------------------------------------------
async def _verify_rdcw(
    slip_image: bytes,
    client_id: str,
    client_secret: str,
    expected_amount: Optional[Decimal] = None,
) -> SlipVerifyResult:
    url = "https://suba.rdcw.co.th/v2/inquiry"

    auth = aiohttp.BasicAuth(client_id, client_secret)

    form = aiohttp.FormData()
    form.add_field("file", slip_image, filename="slip.jpg", content_type="image/jpeg")

    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()

                if resp.status != 200 or not data.get("success"):
                    code = data.get("code")
                    msg = data.get("message", f"HTTP {resp.status}")

                    if code == 1007:
                        return SlipVerifyResult(
                            status=VerifyStatus.QUOTA_EXCEEDED,
                            provider=SlipProvider.RDCW,
                            error_message="RDCW usage quota exceeded",
                            raw_response=data,
                        )

                    return SlipVerifyResult(
                        status=VerifyStatus.SLIP_NOT_FOUND if code in (1004, 1005, 1006) else VerifyStatus.API_ERROR,
                        provider=SlipProvider.RDCW,
                        error_message=msg,
                        raw_response=data,
                    )

                slip_data = data.get("data", {}).get("data", {})

                # RDCW returns amount in satang — convert to THB
                amount_satang = slip_data.get("amount")
                amount_thb = Decimal(str(amount_satang)) / 100 if amount_satang is not None else None

                sender = slip_data.get("sender", {})
                receiver = slip_data.get("receiver", {})

                # Parse date + time
                trans_date = slip_data.get("transDate", "")
                trans_time = slip_data.get("transTime", "")
                timestamp = None
                if trans_date and trans_time:
                    timestamp = _parse_datetime(f"{trans_date}{trans_time.replace(':', '')}")
                elif trans_date:
                    timestamp = _parse_datetime(trans_date)

                return SlipVerifyResult(
                    status=VerifyStatus.VERIFIED,
                    provider=SlipProvider.RDCW,
                    transaction_id=None,  # RDCW doesn't return transRef in v2
                    amount=amount_thb,
                    sender_name=sender.get("name"),
                    receiver_name=receiver.get("name"),
                    timestamp=timestamp,
                    raw_response=data,
                )

    except aiohttp.ClientError as e:
        logger.error("RDCW connection error: %s", e)
        return SlipVerifyResult(
            status=VerifyStatus.API_ERROR,
            provider=SlipProvider.RDCW,
            error_message=str(e),
        )


# ---------------------------------------------------------------------------
# Unified verification — tries all configured providers in order
# ---------------------------------------------------------------------------

_PROVIDER_VERIFIERS = {
    SlipProvider.SLIPOK: _verify_slipok,
    SlipProvider.EASYSLIP: _verify_easyslip,
    SlipProvider.RDCW: _verify_rdcw,
}


def _get_configured_providers() -> list[tuple[SlipProvider, str, str]]:
    """Return list of (provider, key1, key2) for all configured slip APIs."""
    from bot.config.env import EnvKeys

    providers = []

    if EnvKeys.SLIPOK_API_KEY and EnvKeys.SLIPOK_BRANCH_ID:
        providers.append((SlipProvider.SLIPOK, EnvKeys.SLIPOK_API_KEY, EnvKeys.SLIPOK_BRANCH_ID))

    if EnvKeys.EASYSLIP_API_KEY:
        providers.append((SlipProvider.EASYSLIP, EnvKeys.EASYSLIP_API_KEY, ""))

    if EnvKeys.RDCW_CLIENT_ID and EnvKeys.RDCW_CLIENT_SECRET:
        providers.append((SlipProvider.RDCW, EnvKeys.RDCW_CLIENT_ID, EnvKeys.RDCW_CLIENT_SECRET))

    return providers


async def verify_slip(
    slip_image: bytes,
    expected_amount: Optional[Decimal] = None,
    expected_receiver: Optional[str] = None,
) -> SlipVerifyResult:
    """
    Verify a payment slip image via configured Thai slip verification services.

    Tries each configured provider in order (SlipOK → EasySlip → RDCW) until
    one returns a successful verification. Cross-checks amount and receiver
    against expected values.

    Args:
        slip_image: PNG/JPG bytes of the payment slip photo
        expected_amount: Expected payment amount in THB (for cross-check)
        expected_receiver: Expected receiver name (for cross-check)

    Returns:
        SlipVerifyResult with verification status and transaction details
    """
    configured = _get_configured_providers()

    if not configured:
        logger.info("No slip verification APIs configured — skipping auto-verify")
        return SlipVerifyResult(
            status=VerifyStatus.NO_API_CONFIGURED,
            error_message="No slip verification API keys configured. Set SLIPOK/EASYSLIP/RDCW keys in .env",
        )

    last_result = None

    for provider, key1, key2 in configured:
        verifier = _PROVIDER_VERIFIERS[provider]
        logger.info("Attempting slip verification via %s", provider.value)

        result = await verifier(slip_image, key1, key2, expected_amount)

        if result.status == VerifyStatus.VERIFIED:
            # Cross-check amount (if provider didn't already do it)
            if expected_amount is not None and result.amount is not None:
                if abs(result.amount - expected_amount) > Decimal("0.01"):
                    logger.warning(
                        "Slip amount mismatch: expected %s, got %s (provider: %s, txn: %s)",
                        expected_amount, result.amount, provider.value, result.transaction_id,
                    )
                    result.status = VerifyStatus.AMOUNT_MISMATCH
                    result.error_message = (
                        f"Amount mismatch: slip shows {result.amount} THB, "
                        f"expected {expected_amount} THB"
                    )
                    return result

            # Cross-check receiver name
            if expected_receiver and result.receiver_name:
                if expected_receiver.lower() not in result.receiver_name.lower():
                    logger.warning(
                        "Slip receiver mismatch: expected '%s', got '%s'",
                        expected_receiver, result.receiver_name,
                    )
                    result.status = VerifyStatus.RECIPIENT_MISMATCH
                    result.error_message = (
                        f"Receiver mismatch: slip shows '{result.receiver_name}', "
                        f"expected '{expected_receiver}'"
                    )
                    return result

            logger.info(
                "Slip verified via %s — txn: %s, amount: %s, sender: %s",
                provider.value, result.transaction_id, result.amount, result.sender_name,
            )
            return result

        if result.status == VerifyStatus.DUPLICATE:
            # Duplicate is definitive — don't try other providers
            return result

        if result.status == VerifyStatus.QUOTA_EXCEEDED:
            logger.warning("Provider %s quota exceeded, trying next", provider.value)
            last_result = result
            continue

        if result.status == VerifyStatus.API_ERROR:
            logger.warning("Provider %s error, trying next: %s", provider.value, result.error_message)
            last_result = result
            continue

        # SLIP_NOT_FOUND — try next provider
        last_result = result

    return last_result or SlipVerifyResult(
        status=VerifyStatus.SLIP_NOT_FOUND,
        error_message="Slip could not be verified by any configured provider",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string from various API response formats."""
    if not dt_str:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",     # ISO with timezone (EasySlip)
        "%Y-%m-%dT%H:%M:%S",       # ISO no timezone
        "%Y-%m-%d %H:%M:%S",       # Space-separated
        "%Y-%m-%d",                 # Date only (SlipOK)
        "%Y%m%d%H%M%S",            # Compact with time (RDCW)
        "%Y%m%d",                   # Compact date only
    ):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    logger.warning("Could not parse datetime: %s", dt_str)
    return None
