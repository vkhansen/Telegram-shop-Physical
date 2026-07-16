"""CARD-40 Tier C — tickets service parity (TG user_id + web OAuth synthetic id).

Single writer: bot.services.tickets. tickets_web is a facade only.
"""

from __future__ import annotations

from bot.database.main import Database
from bot.database.models.main import Role, SupportTicket, TicketMessage
from bot.platform.capabilities import can, features_for, resolve_capabilities
from bot.platform.identity import PLATFORM_TELEGRAM, PLATFORM_WEB, resolve_user_id
from bot.services import tickets as tickets_svc
from bot.services import tickets_web
from bot.services import web_auth


def _ensure_user_role() -> None:
    with Database().session() as s:
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
            s.commit()


def test_create_list_get_parity_tg_and_web(test_user, db_engine):
    """C1/tests: same service creates/lists tickets for TG id and web synthetic id."""
    _ensure_user_role()
    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="parity-web-tickets",
        email="parity-tickets@example.com",
        email_verified=True,
        display_name="Web Tickets",
        username="webtickets",
    )
    web_uid = int(web["user_id"])
    tg_uid = int(test_user.telegram_id)

    results = []
    for uid, subject in ((tg_uid, "TG help"), (web_uid, "Web help")):
        created = tickets_svc.create_ticket(uid, subject, "Body for " + subject, priority="normal")
        assert created.ok, (uid, created.error_key, created.error_detail)
        assert created.data["ticket_code"]
        assert created.data["id"]
        results.append((uid, created.data))

        listed = tickets_svc.list_tickets(uid)
        assert listed.ok
        assert listed.data["count"] >= 1
        codes = {t["ticket_code"] for t in listed.data["tickets"]}
        assert created.data["ticket_code"] in codes

        detail = tickets_svc.get_ticket(uid, ticket_code=created.data["ticket_code"])
        assert detail.ok
        assert detail.data["ticket"]["subject"] == subject
        assert len(detail.data["ticket"]["messages"]) == 1

        # Other user cannot see
        other = tg_uid if uid == web_uid else web_uid
        assert not tickets_svc.get_ticket(other, ticket_code=created.data["ticket_code"]).ok

    # Domain rows share the SupportTicket table (no dual writer)
    with Database().session() as s:
        rows = s.query(SupportTicket).filter(SupportTicket.user_id.in_([tg_uid, web_uid])).all()
        assert len(rows) >= 2
        assert {r.user_id for r in rows} >= {tg_uid, web_uid}


def test_tickets_web_facade_uses_shared_service(db_engine):
    """tickets_web is not a second writer — same rows as tickets service."""
    _ensure_user_role()
    user = web_auth.upsert_oauth_user(
        provider="dev",
        subject="facade-tickets",
        email="facade@example.com",
        email_verified=True,
        display_name="Facade",
        username="facade",
    )
    uid = int(user["user_id"])

    via_web = tickets_web.create_ticket(uid, "Via web API shape", "Hello from facade")
    assert via_web["ticket_code"]

    via_svc = tickets_svc.get_ticket(uid, ticket_code=via_web["ticket_code"])
    assert via_svc.ok
    assert via_svc.data["ticket"]["subject"] == "Via web API shape"

    listed = tickets_web.list_tickets(uid)
    assert any(t["ticket_code"] == via_web["ticket_code"] for t in listed)

    replied = tickets_web.reply_ticket(uid, via_web["ticket_code"], "More detail")
    assert replied is not None
    assert len(replied["messages"]) == 2

    with Database().session() as s:
        t = s.query(SupportTicket).filter_by(ticket_code=via_web["ticket_code"]).one()
        msgs = s.query(TicketMessage).filter_by(ticket_id=t.id).all()
        assert len(msgs) == 2


def test_reply_and_close_by_id_and_code(test_user, db_engine):
    uid = int(test_user.telegram_id)
    created = tickets_svc.create_ticket(uid, "Close me", "Please close")
    assert created.ok
    tid = created.data["id"]
    code = created.data["ticket_code"]

    r1 = tickets_svc.reply_ticket(uid, "Follow-up", ticket_id=tid)
    assert r1.ok
    r2 = tickets_svc.reply_ticket(uid, "By code", ticket_code=code)
    assert r2.ok

    closed = tickets_svc.close_ticket(uid, ticket_id=tid)
    assert closed.ok
    assert closed.data["status"] == "closed"

    detail = tickets_svc.get_ticket(uid, ticket_code=code)
    assert detail.ok
    assert detail.data["ticket"]["status"] == "closed"
    assert len(detail.data["ticket"]["messages"]) == 3


def test_create_validation():
    res = tickets_svc.create_ticket(1, "", "body")
    assert not res.ok
    assert res.error_key == "ticket.subject_and_message_required"
    res2 = tickets_svc.create_ticket(1, "subj", "  ")
    assert not res2.ok


def test_auth_mask_web_vs_telegram():
    """C4: auth is web OAuth; TG customer mask does not claim OAuth."""
    assert can("web", "auth", role="customer") is True
    # Not in telegram platform ceiling
    assert can("telegram", "auth", role="customer") is False
    assert "auth" not in features_for("telegram", "customer")
    assert "auth" in features_for("web", "customer")

    # Resolved default mask also off for telegram
    tg = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile={},
        channel="telegram",
        role="customer",
    )
    web = resolve_capabilities(
        commerce_mode="full_store",
        age_gate_enabled=False,
        web_profile={"modules": {"show_auth": True}},
        channel="web",
        role="customer",
    )
    assert tg.get("auth") is False
    assert web.get("auth") is True
    # Tickets shared on both
    assert tg.get("tickets") is True
    assert web.get("tickets") is True


def test_identity_edge_resolve_api(test_user, db_engine):
    """C2: resolve API only — TG dual-write + web identity link; no link UI."""
    _ensure_user_role()
    tg_uid = int(test_user.telegram_id)
    from bot.platform.identity import ensure_telegram_identity

    ensure_telegram_identity(tg_uid)
    assert resolve_user_id(PLATFORM_TELEGRAM, str(tg_uid)) == tg_uid

    web = web_auth.upsert_oauth_user(
        provider="dev",
        subject="identity-edge",
        email="edge@example.com",
        email_verified=True,
        display_name="Edge",
        username="edge",
    )
    web_uid = int(web["user_id"])
    # OAuth upsert dual-writes platform=web identity for synthetic uid
    assert resolve_user_id(PLATFORM_WEB, str(web_uid)) == web_uid
    # Tickets service always receives internal user_id (adapter already resolved)
    t = tickets_svc.create_ticket(web_uid, "Identity", "resolved at edge")
    assert t.ok
    assert tickets_svc.list_tickets(web_uid).data["count"] >= 1
