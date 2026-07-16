"""CARD-39 — OAuth user upsert + ticket portal service."""

from bot.services import tickets_web, web_auth


def test_synthetic_id_stable():
    a = web_auth.synthetic_user_id("google", "sub123")
    b = web_auth.synthetic_user_id("google", "sub123")
    assert a == b
    assert a >= 1_000_000_000_000_000


def test_session_roundtrip():
    tok = web_auth.create_session_token(user_id=42, email="a@b.c", name="A")
    data = web_auth.verify_session(tok)
    assert data is not None
    assert data["uid"] == 42
    assert data["email"] == "a@b.c"
    assert web_auth.verify_session("bad.token") is None


def test_upsert_and_tickets(db_engine):
    # roles may be empty — ensure_role_user falls back to 1; create role if needed
    from bot.database.main import Database
    from bot.database.models.main import Role

    with Database().session() as s:
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
            s.commit()

    user = web_auth.upsert_oauth_user(
        provider="dev",
        subject="dev:test@example.com",
        email="test@example.com",
        email_verified=True,
        display_name="Test User",
        username="test",
    )
    uid = user["user_id"]
    assert user["email"] == "test@example.com"

    again = web_auth.upsert_oauth_user(
        provider="dev",
        subject="dev:test@example.com",
        email="test@example.com",
        email_verified=True,
        display_name="Test User 2",
    )
    assert again["user_id"] == uid

    profile = web_auth.get_profile(uid)
    assert profile is not None
    assert profile["email"] == "test@example.com"

    t = tickets_web.create_ticket(uid, "Help", "Something broke")
    assert t["ticket_code"]
    listed = tickets_web.list_tickets(uid)
    assert len(listed) == 1
    detail = tickets_web.get_ticket(uid, t["ticket_code"])
    assert detail is not None
    assert len(detail["messages"]) == 1
    replied = tickets_web.reply_ticket(uid, t["ticket_code"], "More info")
    assert replied is not None
    assert len(replied["messages"]) == 2

    # other user cannot see
    other = web_auth.upsert_oauth_user(
        provider="dev",
        subject="dev:other@example.com",
        email="other@example.com",
        email_verified=True,
        display_name="Other",
    )
    assert tickets_web.get_ticket(other["user_id"], t["ticket_code"]) is None
