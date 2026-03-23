from decimal import Decimal
from typing import Optional, Annotated, Self
from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator
import re


class UserDataUpdate(BaseModel):
    """Validate user data updates"""
    telegram_id: int = Field(..., gt=0)
    balance: Optional[Decimal] = Field(None, ge=0, le=1000000)

    # Removed role_id as it's not used in the current implementation

    @field_validator('balance')
    @classmethod
    def validate_balance(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError('Balance cannot be negative')
        return v


class CategoryRequest(BaseModel):
    """Validate category operations"""
    name: Annotated[str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)]

    def sanitize_name(self) -> str:
        """Sanitize the category name"""
        # Remove any HTML/script tags
        v = re.sub(r'<[^>]*>', '', self.name)
        # Remove multiple spaces
        v = re.sub(r'\s+', ' ', v)
        return v.strip()


class BroadcastMessage(BaseModel):
    """Validate broadcast message"""
    text: Annotated[str, StringConstraints(min_length=1, max_length=4096)]
    parse_mode: Optional[str] = Field("HTML", pattern="^(HTML|Markdown|MarkdownV2)$")

    @model_validator(mode='after')
    def validate_html_tags(self) -> Self:
        """Validate HTML tags after all fields are set"""
        if self.parse_mode == 'HTML':
            # Basic HTML validation - check for balanced tags
            allowed_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a']

            # Simple check for unclosed tags
            for tag in allowed_tags:
                open_count = self.text.count(f'<{tag}>')
                # Also check for tags with attributes
                open_with_attrs = self.text.count(f'<{tag} ')
                total_open = open_count + open_with_attrs
                close_count = self.text.count(f'</{tag}>')

                if total_open != close_count:
                    raise ValueError(f'Unbalanced HTML tag: {tag}')
        return self


class SearchQuery(BaseModel):
    """Validate search queries"""
    query: Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
    limit: int = Field(10, ge=1, le=100)

    # Removed offset as it's not used in the current implementation

    def sanitize_query(self, v: str) -> str:
        """Sanitize the search query"""
        # Remove special characters that could break search
        v = re.sub(r'[^\w\s\-.]', '', self.query)
        return v.strip()


# ---------------------------------------------------------------------------
# Phone number validation & normalisation (Thai-centric, E.164 output)
# ---------------------------------------------------------------------------

_PHONE_STRIP_RE = re.compile(r'[\s\-\(\)]')


def validate_and_normalize_phone(raw: str, default_country_code: str = "66") -> str:
    """Validate a phone number and return its E.164 form.

    Accepted inputs (examples for Thailand, country code 66):
      - "0812345678"   → "+66812345678"   (local with leading 0)
      - "812345678"    → "+66812345678"   (local without leading 0)
      - "+66812345678" → "+66812345678"   (already international)
      - "66812345678"  → "+66812345678"   (international without +)

    Raises ``ValueError`` with a user-friendly reason on invalid input.
    """
    # Strip decorative characters
    phone = _PHONE_STRIP_RE.sub('', raw.strip())

    if not phone:
        raise ValueError("Phone number is empty")

    # Must contain only digits and an optional leading '+'
    if not re.fullmatch(r'\+?\d+', phone):
        raise ValueError("Phone number contains invalid characters")

    # Separate the optional '+' prefix from the digit body
    has_plus = phone.startswith('+')
    digits = phone.lstrip('+')

    if len(digits) < 7 or len(digits) > 15:
        raise ValueError(f"Phone number has {len(digits)} digits; expected 7-15")

    # --- Normalise to E.164 ---
    # Case 1: already has '+' → trust the caller's country code
    if has_plus:
        return f"+{digits}"

    # Case 2: leading '0' → local number, replace 0 with country code
    if digits.startswith('0'):
        digits = digits[1:]  # drop leading 0
        return f"+{default_country_code}{digits}"

    # Case 3: starts with the default country code → treat as international
    if digits.startswith(default_country_code):
        local_part = digits[len(default_country_code):]
        # Thai mobile/landline numbers have 8-9 digits after country code
        if 7 <= len(local_part) <= 10:
            return f"+{digits}"

    # Case 4: bare local number (no leading 0, no country code)
    # Thai numbers without leading 0 are 9 digits (mobile) or 8 digits (landline)
    if 7 <= len(digits) <= 10:
        return f"+{default_country_code}{digits}"

    # If nothing matched, the number is ambiguous — return with country code
    # only if total length is plausible for E.164 (max 15 digits)
    if len(digits) <= 15:
        return f"+{digits}"

    raise ValueError(f"Cannot normalise phone number: {raw!r}")


# Helper functions for validation
def validate_telegram_id(telegram_id) -> int:
    """Validate and convert telegram ID"""
    try:
        tid = int(telegram_id)
        if tid <= 0:
            raise ValueError("Telegram ID must be positive")
        if tid >= 99999999999:  # Max reasonable telegram ID (11 digits)
            raise ValueError("Invalid telegram ID")
        return tid
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid telegram ID: {e}")


def validate_money_amount(amount, min_amount: Decimal = Decimal("0.01"),
                          max_amount: Decimal = Decimal("1000000")) -> Decimal:
    """Validate money amount"""
    try:
        decimal_amount = Decimal(str(amount))

        if decimal_amount < min_amount:
            raise ValueError(f"Amount must be at least {min_amount}")
        if decimal_amount > max_amount:
            raise ValueError(f"Amount cannot exceed {max_amount}")

        # Round to 2 decimal places
        return decimal_amount.quantize(Decimal("0.01"))
    except Exception as e:
        raise ValueError(f"Invalid amount: {e}")


def sanitize_html(text: str) -> str:
    """Sanitize HTML for safe display"""
    # Escape dangerous characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')

    # Allow only safe tags back
    safe_tags = {
        '&lt;b&gt;': '<b>', '&lt;/b&gt;': '</b>',
        '&lt;i&gt;': '<i>', '&lt;/i&gt;': '</i>',
        '&lt;u&gt;': '<u>', '&lt;/u&gt;': '</u>',
        '&lt;code&gt;': '<code>', '&lt;/code&gt;': '</code>',
    }

    for escaped, original in safe_tags.items():
        text = text.replace(escaped, original)

    return text
