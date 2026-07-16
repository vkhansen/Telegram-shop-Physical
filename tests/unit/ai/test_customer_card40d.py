"""CARD-40 Tier D — Grok as masked adapter (services + caps + Messenger)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from bot.ai import customer_executor as exec_mod
from bot.ai.customer_schemas import (
    BrowseMenuAction,
    GetOrderStatusAction,
    OpenSupportTicketAction,
    StartAppLiveChatAction,
)
from bot.ai.customer_tool_defs import (
    CUSTOMER_TOOLS,
    TOOL_REQUIRED_CAP,
    tool_allowed,
    tools_for_capabilities,
    tools_for_channel,
)
from bot.database.main import Database
from bot.database.models.main import SupportTicket, TicketMessage
from bot.platform.capabilities import resolve_capabilities
from bot.platform.messaging import RecordingMessenger, set_messenger
from bot.services import order_query as order_query_svc
from bot.services import tickets as tickets_svc


def _tool_names(tools: list[dict]) -> set[str]:
    return {t["function"]["name"] for t in tools}


def test_tools_for_telegram_includes_shared_caps():
    """D2: default TG customer mask exposes catalog / order / tickets tools."""
    tools = tools_for_channel("telegram")
    names = _tool_names(tools)
    assert "browse_menu" in names
    assert "get_order_status" in names
    assert "open_support_ticket" in names
    assert "start_app_live_chat" in names
    # leads/booking tools do not exist on customer assistant (and must not appear)
    assert "create_lead" not in names
    assert "book_slot" not in names


def test_tools_mask_off_tickets_and_ai():
    """D2: tickets/order tools disappear when caps off; empty when ai_customer off."""
    caps = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile=None,
        channel="telegram",
    )
    caps["tickets"] = False
    names = _tool_names(tools_for_capabilities(caps))
    assert "open_support_ticket" not in names
    assert "start_store_live_chat" not in names
    assert "browse_menu" in names  # catalog still on

    caps["ai_customer"] = False
    assert tools_for_capabilities(caps) == []
    assert not tool_allowed("browse_menu", caps)


def test_tools_mask_off_catalog_and_location():
    caps = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile=None,
        channel="telegram",
    )
    caps["catalog"] = False
    caps["location_once"] = False
    caps["checkout"] = False
    names = _tool_names(tools_for_capabilities(caps))
    assert "browse_menu" not in names
    assert "get_today_specials" not in names
    assert "find_deals" not in names
    assert "find_nearby_stores" not in names
    assert "check_coupon" not in names
    assert "get_order_status" in names
    assert "open_support_ticket" in names


def test_every_customer_tool_has_cap_mapping():
    names = _tool_names(CUSTOMER_TOOLS)
    assert names == set(TOOL_REQUIRED_CAP.keys())


def test_browse_menu_uses_catalog_service(test_goods, db_engine):
    """D1: catalog browse goes through customer_catalog service."""
    res = exec_mod.execute_browse_menu(BrowseMenuAction(keyword="Test", limit=5))
    assert res["count"] >= 1
    assert any(i["name"] == test_goods.name for i in res["items"])


def test_get_order_status_uses_order_query(test_user, test_order, db_engine):
    """D1: order status via order_query service (own orders only)."""
    uid = test_user.telegram_id
    listed = exec_mod.execute_get_order_status(GetOrderStatusAction(limit=5), uid)
    assert listed["orders"]
    codes = {o["order_code"] for o in listed["orders"]}
    assert test_order.order_code in codes

    by_code = exec_mod.execute_get_order_status(
        GetOrderStatusAction(order_code=test_order.order_code), uid
    )
    assert by_code["orders"][0]["order_code"] == test_order.order_code

    # Other user sees nothing
    empty = exec_mod.execute_get_order_status(
        GetOrderStatusAction(order_code=test_order.order_code), uid + 1
    )
    assert empty["orders"] == []


@pytest.mark.asyncio
async def test_open_support_ticket_uses_tickets_service_and_messenger(test_user, db_engine):
    """D1/D4: AI open ticket → services.tickets single writer + Messenger notify."""
    rec = RecordingMessenger()
    set_messenger(rec)
    try:
        with patch.object(exec_mod, "_get_maintainer_ids", return_value=[999001]):
            action = OpenSupportTicketAction(
                subject="AI help needed now",
                description="Something broke in checkout flow please help",
                priority="high",
            )
            result = await exec_mod.execute_open_support_ticket(action, test_user.telegram_id)
        assert result["success"] is True
        code = result["ticket_code"]
        assert code

        # Same row as tickets service
        detail = tickets_svc.get_ticket(test_user.telegram_id, ticket_code=code)
        assert detail.ok
        assert detail.data["ticket"]["subject"] == "AI help needed now"
        assert len(detail.data["ticket"]["messages"]) == 1

        with Database().session() as s:
            row = s.query(SupportTicket).filter_by(ticket_code=code).one()
            assert row.user_id == test_user.telegram_id
            msgs = s.query(TicketMessage).filter_by(ticket_id=row.id).all()
            assert len(msgs) == 1

        assert any("New Support Ticket" in t["text"] for t in rec.texts)
        assert any(t["user_ref"] == 999001 for t in rec.texts)
    finally:
        set_messenger(None)


@pytest.mark.asyncio
async def test_open_ticket_linked_order_only_own(test_user, test_order, db_engine):
    from bot.services import web_auth

    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="other-order-link",
        email="other-order@example.com",
        email_verified=True,
        display_name="Other",
        username="otherorder",
    )
    other_uid = int(web["user_id"])

    rec = RecordingMessenger()
    set_messenger(rec)
    try:
        with patch.object(exec_mod, "_get_maintainer_ids", return_value=[]):
            ok = await exec_mod.execute_open_support_ticket(
                OpenSupportTicketAction(
                    subject="Order problem here",
                    description="My order never arrived at the address",
                    order_code=test_order.order_code,
                ),
                test_user.telegram_id,
            )
            assert ok["success"]
            detail = tickets_svc.get_ticket(
                test_user.telegram_id, ticket_code=ok["ticket_code"]
            )
            assert detail.ok
            assert detail.data["ticket"]["order_id"] == test_order.id

            # Other user cannot attach someone else's order_code
            other = await exec_mod.execute_open_support_ticket(
                OpenSupportTicketAction(
                    subject="Spoof order attempt",
                    description="Trying to attach someone elses order code",
                    order_code=test_order.order_code,
                ),
                other_uid,
            )
            assert other["success"]
            d2 = tickets_svc.get_ticket(other_uid, ticket_code=other["ticket_code"])
            assert d2.ok
            assert d2.data["ticket"]["order_id"] is None
    finally:
        set_messenger(None)


@pytest.mark.asyncio
async def test_live_chat_create_uses_tickets_service(test_user, db_engine):
    rec = RecordingMessenger()
    set_messenger(rec)
    try:
        with patch.object(exec_mod, "_get_maintainer_ids", return_value=[42]):
            result = await exec_mod.execute_start_app_live_chat(
                StartAppLiveChatAction(reason="Bot payment screen freezes"),
                test_user.telegram_id,
            )
        assert result["success"] is True
        assert result["ticket_id"]
        assert result["ticket_code"]

        detail = tickets_svc.get_ticket(
            test_user.telegram_id, ticket_id=result["ticket_id"]
        )
        assert detail.ok
        assert "[APP_LIVE_CHAT]" in detail.data["ticket"]["subject"]

        # Append via service (live chat path)
        app = tickets_svc.append_message(
            test_user.telegram_id,
            "Still broken after restart",
            ticket_id=result["ticket_id"],
        )
        assert app.ok
        detail2 = tickets_svc.get_ticket(
            test_user.telegram_id, ticket_id=result["ticket_id"]
        )
        assert len(detail2.data["ticket"]["messages"]) == 2

        assert any("App Live Chat" in t["text"] for t in rec.texts)
    finally:
        set_messenger(None)


def test_order_query_is_single_source_for_ai(test_user, test_order, db_engine):
    """AI path and order_query return the same codes for the same user."""
    svc = order_query_svc.list_orders(test_user.telegram_id, limit=10)
    ai = exec_mod.execute_get_order_status(
        GetOrderStatusAction(limit=10), test_user.telegram_id
    )
    assert svc.ok
    svc_codes = {o["order_code"] for o in svc.data["orders"]}
    ai_codes = {o["order_code"] for o in ai["orders"]}
    assert svc_codes == ai_codes
