"""CARD-36 leads + bookings."""

from bot.database.main import Database
from bot.database.models.main import Brand, Role
from bot.services import leads_bookings


def test_create_lead_and_booking(db_engine):
    with Database().session() as s:
        if s.query(Role).filter_by(name="USER").first() is None:
            s.add(Role(name="USER", permissions=1))
        s.add(Brand(name="Lead Co", slug="lead-co", description="d"))
        s.commit()

    lead = leads_bookings.create_lead(
        brand_slug="lead-co",
        name="Ada",
        phone="+66811112222",
        preferred_channel="line",
        message="Interested",
        consent=True,
        item_slug="widget",
    )
    assert lead["id"]
    assert lead["status"] == "new"

    booking = leads_bookings.create_booking(
        brand_slug="lead-co",
        name="Ada",
        phone="+66811112222",
        meeting_type="google_meet",
        preferred_when="2026-08-01T10:00",
        notes="Discuss portfolio",
    )
    assert booking["id"]
    assert booking["meeting_type"] == "google_meet"
    assert booking["status"] == "requested"


def test_lead_requires_consent(db_engine):
    with Database().session() as s:
        s.add(Brand(name="Lead Co2", slug="lead-co-2"))
        s.commit()
    try:
        leads_bookings.create_lead(
            brand_slug="lead-co-2",
            name="Bob",
            email="b@example.com",
            consent=False,
        )
        assert False, "expected ValueError"
    except ValueError as e:
        assert "consent" in str(e)
