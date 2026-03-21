"""
PromptPay QR code generation for Thai bank payments (Card 1).

Generates EMVCo-standard QR codes that work with all Thai banking apps
(SCB, KBank, Bangkok Bank, TrueMoney, etc.).
"""
import io
import logging
from decimal import Decimal

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
