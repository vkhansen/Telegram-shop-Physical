"""Per-store payment-target resolution (Card 28).

Resolves *which PromptPay account an order pays into* and *which receiver name a
slip is verified against*, with precedence **store → brand → global setting**.

This is deliberately the single source of truth used by BOTH the QR-generation
path and the slip-verification path in ``order_handler.py`` — so the account the
customer scans/pays and the account we verify the uploaded slip against can
never diverge. (Before Card 28 the QR used a global id and verification used a
global name; per-store accounts would have silently mismatched.)
"""

from dataclasses import dataclass

from bot.database.main import Database
from bot.database.models.main import Brand, Store


@dataclass(frozen=True)
class PaymentTarget:
    """Where an order's PromptPay payment should go and how to verify its slip."""

    promptpay_id: str = ""  # "" if no dynamic id configured anywhere
    promptpay_name: str = ""  # account name → expected slip receiver
    static_qr_file_id: str | None = None  # store's pre-made static QR image, if any
    source: str = "global"  # "store" | "brand" | "global" (for logging/tests)


def resolve_payment_target(store_id: int | None = None, brand_id: int | None = None) -> PaymentTarget:
    """Resolve the PromptPay target for an order, store → brand → global.

    A store "wins" if it has either its own dynamic PromptPay id *or* a static
    QR image (an explicit branch-level payment setup). Otherwise the brand's
    PromptPay id is used, then the global bot setting / env var.
    """
    if store_id:
        with Database().session() as s:
            store = s.query(Store).filter(Store.id == store_id).one_or_none()
            if store and (store.promptpay_id or store.payment_qr_file_id):
                return PaymentTarget(
                    promptpay_id=store.promptpay_id or "",
                    promptpay_name=store.promptpay_name or "",
                    static_qr_file_id=store.payment_qr_file_id,
                    source="store",
                )

    if brand_id:
        with Database().session() as s:
            brand = s.query(Brand).filter(Brand.id == brand_id).one_or_none()
            if brand and brand.promptpay_id:
                return PaymentTarget(
                    promptpay_id=brand.promptpay_id,
                    promptpay_name=brand.promptpay_name or "",
                    source="brand",
                )

    # Global fallback — lazy import avoids a module-load cycle with the admin handler.
    from bot.handlers.admin.settings_management import get_promptpay_id, get_promptpay_name

    return PaymentTarget(
        promptpay_id=get_promptpay_id() or "",
        promptpay_name=get_promptpay_name() or "",
        source="global",
    )


def get_store_menu_image(store_id: int | None) -> str | None:
    """Return a store's menu-board image file_id, or None."""
    if not store_id:
        return None
    with Database().session() as s:
        store = s.query(Store).filter(Store.id == store_id).one_or_none()
        return store.menu_image_file_id if store else None
