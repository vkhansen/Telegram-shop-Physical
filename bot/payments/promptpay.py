"""
PromptPay QR code generation and parsing for Thai bank payments (Card 1).

Generates EMVCo-standard QR codes that work with all Thai banking apps
(SCB, KBank, Bangkok Bank, TrueMoney, etc.).
Also decodes/parses QR images to extract PromptPay IDs.
"""
import io
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def generate_promptpay_payload(promptpay_id: str, amount: Decimal) -> str:
    """
    Generate EMVCo PromptPay payload string.

    Args:
        promptpay_id: Phone number (0812345678) or national ID (1234567890123)
        amount: Payment amount in THB (must be > 0)

    Returns:
        EMVCo payload string for QR encoding

    Raises:
        ValueError: If promptpay_id or amount is invalid
    """
    if not promptpay_id or not promptpay_id.strip():
        raise ValueError("PromptPay ID is required")

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    # Clean the ID
    clean_id = promptpay_id.strip().replace("-", "").replace(" ", "")

    # Determine ID type and format
    if len(clean_id) == 10 and clean_id.startswith("0"):
        # Phone number: convert 0812345678 → 0066812345678
        aid = "A000000677010111"
        formatted_id = "0066" + clean_id[1:]
    elif len(clean_id) == 13:
        # National ID
        aid = "A000000677010112"
        formatted_id = clean_id
    else:
        raise ValueError(
            f"Invalid PromptPay ID '{promptpay_id}': must be 10-digit phone or 13-digit national ID"
        )

    # Build EMVCo payload
    def tlv(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    # Merchant account info (tag 29)
    merchant_info = tlv("00", aid) + tlv("01", formatted_id)

    payload_parts = [
        tlv("00", "01"),              # Payload format indicator
        tlv("01", "11"),              # Point of sale (static QR)
        tlv("29", merchant_info),     # Merchant account info
        tlv("53", "764"),             # Transaction currency (THB)
        tlv("54", str(amount)),       # Transaction amount
        tlv("58", "TH"),             # Country code
    ]

    payload_without_crc = "".join(payload_parts) + "6304"

    # Calculate CRC-16/CCITT-FALSE
    crc = _crc16(payload_without_crc)

    return payload_without_crc + f"{crc:04X}"


def _crc16(data: str) -> int:
    """Calculate CRC-16/CCITT-FALSE checksum"""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def generate_promptpay_qr(promptpay_id: str, amount: Decimal) -> bytes:
    """
    Generate PromptPay QR code as PNG bytes.

    Args:
        promptpay_id: Phone number or national ID
        amount: Payment amount in THB

    Returns:
        PNG image bytes of the QR code

    Raises:
        ValueError: If inputs are invalid
        ImportError: If qrcode library not installed
    """
    try:
        import qrcode
    except ImportError as e:
        raise ImportError(
            "qrcode library required for PromptPay QR. Install with: pip install qrcode[pil]"
        ) from e

    payload = generate_promptpay_payload(promptpay_id, amount)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


# ---------------------------------------------------------------------------
# EMVCo TLV Parser — reverse of generate_promptpay_payload
# ---------------------------------------------------------------------------

# PromptPay AID → ID type mapping
_AID_PHONE = "A000000677010111"
_AID_NATIONAL_ID = "A000000677010112"


@dataclass
class PromptPayInfo:
    """Extracted PromptPay account info from a QR payload."""
    promptpay_id: str           # Phone (0812345678) or national ID (1234567890123)
    id_type: str                # "phone" or "national_id"
    amount: Optional[Decimal]   # None for static QR (no amount embedded)
    country_code: Optional[str]
    currency_code: Optional[str]
    raw_payload: str


def parse_emvco_tlv(payload: str) -> dict[str, str]:
    """
    Parse EMVCo TLV (Tag-Length-Value) payload string into a dict.

    Each field: 2-char tag + 2-char length (decimal) + value of that length.
    Returns dict mapping tag → value.
    """
    result = {}
    pos = 0
    while pos + 4 <= len(payload):
        tag = payload[pos:pos + 2]
        try:
            length = int(payload[pos + 2:pos + 4])
        except ValueError:
            break
        value = payload[pos + 4:pos + 4 + length]
        if len(value) < length:
            break
        result[tag] = value
        pos += 4 + length
    return result


def parse_promptpay_payload(payload: str) -> PromptPayInfo:
    """
    Parse an EMVCo PromptPay QR payload string and extract account info.

    Args:
        payload: Raw EMVCo payload string (from QR code data)

    Returns:
        PromptPayInfo with extracted account details

    Raises:
        ValueError: If payload is not a valid PromptPay QR
    """
    if not payload or len(payload) < 20:
        raise ValueError("Payload too short to be a valid EMVCo QR")

    tlv = parse_emvco_tlv(payload)

    # Tag 29 = PromptPay merchant account info (could also be 29 or 30)
    merchant_data = None
    for tag in ("29", "30"):
        if tag in tlv:
            merchant_data = tlv[tag]
            break

    if not merchant_data:
        raise ValueError("No PromptPay merchant info found (tag 29/30 missing)")

    # Parse nested TLV inside merchant account info
    merchant_tlv = parse_emvco_tlv(merchant_data)

    aid = merchant_tlv.get("00", "")
    raw_id = merchant_tlv.get("01", "")

    if not raw_id:
        # Some QR formats use tag 02 or 03 for the ID
        raw_id = merchant_tlv.get("02", "") or merchant_tlv.get("03", "")

    if not raw_id:
        raise ValueError("No PromptPay ID found in merchant data")

    # Determine ID type and convert back to local format
    if aid == _AID_PHONE or (raw_id.startswith("0066") and len(raw_id) == 13):
        # International phone → local: 0066812345678 → 0812345678
        local_id = "0" + raw_id[4:] if raw_id.startswith("0066") else raw_id
        id_type = "phone"
    elif aid == _AID_NATIONAL_ID or len(raw_id) == 13:
        local_id = raw_id
        id_type = "national_id"
    else:
        # Unknown format — return as-is
        local_id = raw_id
        id_type = "unknown"

    # Extract amount (tag 54) — may be absent for static QR
    amount = None
    if "54" in tlv:
        try:
            amount = Decimal(tlv["54"])
        except (ValueError, TypeError, ArithmeticError) as e:
            logging.getLogger(__name__).warning("Failed to parse PromptPay amount tag 54: %s (value: %s)", e, tlv["54"])

    return PromptPayInfo(
        promptpay_id=local_id,
        id_type=id_type,
        amount=amount,
        country_code=tlv.get("58"),
        currency_code=tlv.get("53"),
        raw_payload=payload,
    )


def decode_qr_image(image_bytes: bytes) -> str:
    """
    Decode QR code data from an image.

    Tries pyzbar first, falls back to OpenCV QR detector.

    Args:
        image_bytes: PNG/JPG image bytes

    Returns:
        Decoded QR data string

    Raises:
        ValueError: If no QR code found in image
        ImportError: If neither pyzbar nor opencv-python is installed
    """
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))

    # Try pyzbar first (more reliable for various QR formats)
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        results = pyzbar_decode(img)
        if results:
            return results[0].data.decode("utf-8")
    except ImportError:
        pass

    # Fallback: OpenCV QR detector
    try:
        import cv2
        import numpy as np

        # Convert PIL to OpenCV format
        img_array = np.array(img.convert("RGB"))
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_cv)
        if data:
            return data
    except ImportError:
        pass

    # Neither library available
    try:
        from pyzbar.pyzbar import decode as _  # noqa: F401
    except ImportError:
        try:
            import cv2  # noqa: F401
        except ImportError:
            raise ImportError(
                "QR decoding requires pyzbar or opencv-python. "
                "Install with: pip install pyzbar  or  pip install opencv-python"
            )

    raise ValueError("No QR code found in the image")


def extract_promptpay_from_image(image_bytes: bytes) -> PromptPayInfo:
    """
    Extract PromptPay account info from a QR code image.

    Decodes the QR image, then parses the EMVCo payload.

    Args:
        image_bytes: PNG/JPG image bytes of a PromptPay QR code

    Returns:
        PromptPayInfo with extracted account details

    Raises:
        ValueError: If image doesn't contain a valid PromptPay QR
        ImportError: If QR decoding libraries not installed
    """
    qr_data = decode_qr_image(image_bytes)
    logger.info("Decoded QR data: %s...", qr_data[:40] if len(qr_data) > 40 else qr_data)
    return parse_promptpay_payload(qr_data)
