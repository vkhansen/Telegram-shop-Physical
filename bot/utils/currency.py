from decimal import Decimal

from bot.config.env import EnvKeys


def format_currency(amount: Decimal) -> str:
    """
    Format amount with currency symbol.

    For THB: ฿1,234.00
    For other currencies: 1,234.00 USD
    """
    amount = Decimal(str(amount))
    currency = EnvKeys.PAY_CURRENCY

    if currency == "THB":
        return f"฿{amount:,.2f}"

    return f"{amount:,.2f} {currency}"
