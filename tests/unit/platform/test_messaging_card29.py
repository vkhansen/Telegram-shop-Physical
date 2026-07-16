"""CARD-29 — Messenger port + notifications wiring."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.platform.messaging import (
    ButtonSpec,
    RecordingMessenger,
    get_messenger,
    set_messenger,
)
from bot.platform.telegram_messenger import TelegramMessenger, _resolve_group_chat_id


@pytest.fixture(autouse=True)
def _reset_messenger():
    set_messenger(None)
    yield
    set_messenger(None)


def test_get_messenger_defaults_to_telegram():
    m = get_messenger()
    assert isinstance(m, TelegramMessenger)


def test_set_messenger_override():
    fake = RecordingMessenger()
    set_messenger(fake)
    assert get_messenger() is fake


@pytest.mark.asyncio
async def test_recording_messenger_records_calls():
    fake = RecordingMessenger()
    assert await fake.send_text(42, "hi") is True
    assert await fake.send_photo(42, "file_id", caption="cap") is True
    mid = await fake.send_group("kitchen", "order up", buttons=ButtonSpec(native="kb"))
    assert mid == "1"
    assert fake.texts[0]["user_ref"] == 42
    assert fake.photos[0]["photo"] == "file_id"
    assert fake.groups[0]["group_key"] == "kitchen"


def test_resolve_group_chat_id_named_and_raw():
    with patch("bot.platform.telegram_messenger.EnvKeys") as env:
        env.KITCHEN_GROUP_ID = "-100111"
        env.RIDER_GROUP_ID = "-100222"
        assert _resolve_group_chat_id("kitchen") == -100111
        assert _resolve_group_chat_id("rider") == -100222
    assert _resolve_group_chat_id("-100333") == -100333
    assert _resolve_group_chat_id("") is None


@pytest.mark.asyncio
async def test_telegram_messenger_send_text_uses_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    m = TelegramMessenger(bot=bot)
    ok = await m.send_text(99, "<b>hi</b>", buttons=ButtonSpec(native="markup"))
    assert ok is True
    bot.send_message.assert_awaited_once()
    kwargs = bot.send_message.await_args.kwargs
    assert kwargs["chat_id"] == 99
    assert kwargs["text"] == "<b>hi</b>"
    assert kwargs["reply_markup"] == "markup"


@pytest.mark.asyncio
async def test_telegram_messenger_send_group_returns_message_id():
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=SimpleNamespace(message_id=777))
    m = TelegramMessenger(bot=bot)
    with patch("bot.platform.telegram_messenger.EnvKeys") as env:
        env.KITCHEN_GROUP_ID = "-1001"
        mid = await m.send_group("kitchen", "prep")
    assert mid == "777"


@pytest.mark.asyncio
async def test_notify_order_confirmed_uses_messenger():
    from bot.payments import notifications as notif

    fake = RecordingMessenger()
    set_messenger(fake)
    order = SimpleNamespace(
        buyer_id=12345,
        order_code="ABC123",
        total_price=100,
    )
    item = SimpleNamespace(item_name="Tea", quantity=1, price=100)
    ok = await notif.notify_order_confirmed(order, [item], datetime(2026, 1, 2, 15, 30))
    assert ok is True
    assert len(fake.texts) == 1
    assert fake.texts[0]["user_ref"] == 12345
    assert "ABC123" in fake.texts[0]["text"]


@pytest.mark.asyncio
async def test_send_delivery_photo_uses_messenger():
    from bot.payments import notifications as notif

    fake = RecordingMessenger()
    set_messenger(fake)
    order = SimpleNamespace(buyer_id=7, order_code="ZZ", delivery_photo="AgAC_photo")
    ok = await notif.send_delivery_photo_to_customer(order)
    assert ok is True
    assert fake.photos[0]["photo"] == "AgAC_photo"
    assert fake.photos[0]["user_ref"] == 7


@pytest.mark.asyncio
async def test_notify_kitchen_group_uses_messenger_group():
    from bot.payments import notifications as notif

    fake = RecordingMessenger()
    set_messenger(fake)
    order = SimpleNamespace(
        id=1,
        order_code="K1",
        total_price=50,
        delivery_address="A",
        phone_number="1",
    )
    item = SimpleNamespace(item_name="Soup", quantity=1, price=50)
    with patch("bot.keyboards.inline.kitchen_order_keyboard", return_value="kb"):
        mid = await notif.notify_kitchen_group(None, order, [item])
    assert mid == 1
    assert fake.groups[0]["group_key"] == "kitchen"
    assert "K1" in fake.groups[0]["text"]


def test_notifications_no_direct_get_shared_bot_calls():
    """Static: notify helpers re-export get_shared_bot but must not call it."""
    import ast
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "bot" / "payments" / "notifications.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == "get_shared_bot":
                offenders.append(getattr(node, "lineno", 0))
    assert offenders == [], f"get_shared_bot still called in notifications.py: {offenders}"
