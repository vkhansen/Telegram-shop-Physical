"""
CARD-23 — Payment Handler DB-Session Refactor.

Two kinds of guard:

1. A static (AST) guard that encodes the card's core acceptance criterion:
   none of the payment/order-creation handlers may hold a
   ``with Database().session()`` block open across an ``await``. This is the
   structural property that prevents pool exhaustion under load, and it is
   cheap and deterministic to assert.

2. Functional tests over ``process_cash_payment_new_message`` — the simplest
   order-creation handler (no address pool, no QR, no network) — covering the
   five scenarios named in the card: happy path, customer-not-found,
   insufficient bonus, reservation failure, and a post-commit Telegram failure
   (the order must survive a failed outbound send).
"""

import ast
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.database.main import Database
from bot.database.models.main import Order, ShoppingCart

ORDER_HANDLER_PATH = Path(__file__).resolve().parents[2] / "bot" / "handlers" / "user" / "order_handler.py"

# Handlers refactored under CARD-23 (and its whole-class extension).
REFACTORED_HANDLERS = {
    "process_crypto_payment",
    "process_bitcoin_payment_new_message",
    "process_bitcoin_payment",
    "process_cash_payment_new_message",
    "process_promptpay_payment",
    "process_receipt_photo",
}


# ---------------------------------------------------------------------------
# 1. Static guard — no await inside a Database().session() block
# ---------------------------------------------------------------------------
def _is_db_session_with(node: ast.With) -> bool:
    """True if this ``with`` opens a ``Database().session()`` context."""
    for item in node.items:
        expr = item.context_expr
        # match `Database().session()` → Call(func=Attribute(attr="session", ...))
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "session":
            return True
    return False


def _awaits_inside(node: ast.With) -> list[int]:
    """Line numbers of any ``await`` expression nested in this ``with`` block."""
    return [child.lineno for child in ast.walk(node) if isinstance(child, ast.Await)]


def _function_defs(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            yield node


@pytest.mark.unit
def test_no_await_inside_db_session_blocks():
    """CARD-23: every refactored handler must release its DB session before awaiting."""
    tree = ast.parse(ORDER_HANDLER_PATH.read_text(encoding="utf-8"))

    offenders: dict[str, list[int]] = {}
    seen: set[str] = set()
    for fn in _function_defs(tree):
        if fn.name not in REFACTORED_HANDLERS:
            continue
        seen.add(fn.name)
        for node in ast.walk(fn):
            if isinstance(node, ast.With) and _is_db_session_with(node):
                awaits = _awaits_inside(node)
                if awaits:
                    offenders.setdefault(fn.name, []).extend(awaits)

    assert not offenders, f"await found inside a Database().session() block (pool-exhaustion risk): {offenders}"
    # Guard against the handlers being renamed out from under this test.
    missing = REFACTORED_HANDLERS - seen
    assert not missing, f"expected handlers not found in order_handler.py: {missing}"


# ---------------------------------------------------------------------------
# 2. Functional scenarios over process_cash_payment_new_message
# ---------------------------------------------------------------------------
CART_ITEMS = [
    {
        "item_name": "Test Product",
        "quantity": 2,
        "price": Decimal("99.99"),
        "total": Decimal("199.98"),
    }
]


def _make_message(user_id: int):
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.answer = AsyncMock()
    message.bot = MagicMock()
    return message


def _make_state(data: dict | None = None):
    state = MagicMock()
    state.get_data = AsyncMock(return_value=data or {})
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


def _patch_handler_io(total=Decimal("199.98"), cart=None, reserve=None):
    """Patch the async/I-O collaborators of order_handler, leaving the DB real."""
    cart = CART_ITEMS if cart is None else cart
    patches = [
        patch("bot.handlers.user.order_handler.get_telegram_username", new=AsyncMock(return_value="tester")),
        patch("bot.handlers.user.order_handler.get_cart_items", new=AsyncMock(return_value=cart)),
        patch("bot.handlers.user.order_handler.calculate_cart_total", new=AsyncMock(return_value=total)),
        patch("bot.handlers.user.order_handler.notify_admin_new_cash_order", new=AsyncMock()),
        patch("bot.handlers.user.order_handler.sync_customer_to_csv", new=MagicMock()),
    ]
    if reserve is not None:
        patches.append(patch("bot.handlers.user.order_handler.reserve_inventory", new=MagicMock(return_value=reserve)))
    return patches


def _enter(patches):
    return [p.__enter__() for p in patches]


def _exit(patches):
    for p in reversed(patches):
        p.__exit__(None, None, None)


def _orders_for(user_id: int) -> list[Order]:
    with Database().session() as session:
        return session.query(Order).filter_by(buyer_id=user_id).all()


@pytest.mark.asyncio
@pytest.mark.payments
async def test_cash_happy_path_creates_order_and_clears_cart(test_customer_info, test_goods, db_session):
    from bot.handlers.user.order_handler import process_cash_payment_new_message

    user_id = test_customer_info.telegram_id
    # Seed a cart row so we can assert it is cleared.
    db_session.add(ShoppingCart(user_id=user_id, item_name=test_goods.name, quantity=2))
    db_session.commit()

    patches = _patch_handler_io()
    _enter(patches)
    try:
        message, state = _make_message(user_id), _make_state({})
        await process_cash_payment_new_message(message, state, user_id=user_id)
    finally:
        _exit(patches)

    orders = _orders_for(user_id)
    assert len(orders) == 1
    assert orders[0].payment_method == "cash"
    # reserve_inventory ran and transitioned the order off "pending".
    assert orders[0].order_status == "reserved"
    assert orders[0].order_code
    # Outbound I/O happened in phase 3, after the session closed.
    message.answer.assert_awaited()
    state.clear.assert_awaited_once()
    # Cart cleared.
    with Database().session() as session:
        assert session.query(ShoppingCart).filter_by(user_id=user_id).count() == 0


@pytest.mark.asyncio
@pytest.mark.payments
async def test_cash_customer_not_found_creates_no_order(db_with_roles):
    from bot.handlers.user.order_handler import process_cash_payment_new_message

    user_id = 555000111  # no CustomerInfo row for this id
    patches = _patch_handler_io()
    _enter(patches)
    try:
        message, state = _make_message(user_id), _make_state({})
        await process_cash_payment_new_message(message, state, user_id=user_id)
    finally:
        _exit(patches)

    assert _orders_for(user_id) == []
    message.answer.assert_awaited_once()  # the customer_not_found message
    state.clear.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.payments
async def test_cash_insufficient_bonus_creates_no_order_and_keeps_balance(test_customer_info, test_goods):
    from bot.handlers.user.order_handler import process_cash_payment_new_message

    user_id = test_customer_info.telegram_id  # bonus_balance == 0 from fixture
    patches = _patch_handler_io()
    _enter(patches)
    try:
        message, state = _make_message(user_id), _make_state({"bonus_applied": 50})
        await process_cash_payment_new_message(message, state, user_id=user_id)
    finally:
        _exit(patches)

    assert _orders_for(user_id) == []
    state.clear.assert_not_called()
    # Bonus balance untouched.
    with Database().session() as session:
        from bot.database.models.main import CustomerInfo

        ci = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
        assert ci.bonus_balance == Decimal("0")


@pytest.mark.asyncio
@pytest.mark.payments
async def test_cash_reserve_failure_rolls_back_order(test_customer_info, test_goods):
    from bot.handlers.user.order_handler import process_cash_payment_new_message

    user_id = test_customer_info.telegram_id
    patches = _patch_handler_io(reserve=(False, "Out of stock"))
    _enter(patches)
    try:
        message, state = _make_message(user_id), _make_state({})
        await process_cash_payment_new_message(message, state, user_id=user_id)
    finally:
        _exit(patches)

    # Order was added + flushed, then rolled back on reservation failure.
    assert _orders_for(user_id) == []
    message.answer.assert_awaited_once()  # unable_to_reserve message
    state.clear.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.payments
async def test_cash_post_commit_telegram_failure_keeps_order(test_customer_info, test_goods):
    from bot.handlers.user.order_handler import process_cash_payment_new_message

    user_id = test_customer_info.telegram_id
    patches = _patch_handler_io()
    _enter(patches)
    try:
        message, state = _make_message(user_id), _make_state({})
        # The phase-3 payment-text send fails *after* the order is committed.
        message.answer = AsyncMock(side_effect=RuntimeError("telegram down"))
        with pytest.raises(RuntimeError):
            await process_cash_payment_new_message(message, state, user_id=user_id)
    finally:
        _exit(patches)

    # Order survives a failed outbound send — it was already committed.
    orders = _orders_for(user_id)
    assert len(orders) == 1
    assert orders[0].order_code
