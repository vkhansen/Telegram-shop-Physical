"""Per-store menu image on selection + admin asset management (Card 28)."""

from types import SimpleNamespace

import pytest

from bot.database.main import Database
from bot.database.models.main import Brand, Store


# ── Fakes ────────────────────────────────────────────────────────────────────
class FakeState:
    def __init__(self, data=None):
        self._d = dict(data or {})

    async def get_data(self):
        return dict(self._d)

    async def update_data(self, **kw):
        self._d.update(kw)

    async def set_state(self, *a, **k):
        pass

    async def clear(self):
        self._d.clear()


class FakeMessageObj:
    """Stands in for call.message (answer_photo / edit_text) and Message (answer)."""

    def __init__(self):
        self.photos = []
        self.answers = []

    async def answer_photo(self, photo, caption=None, **k):
        self.photos.append((photo, caption))

    async def edit_text(self, *a, **k):
        pass

    async def answer(self, *a, **k):
        self.answers.append((a, k))


class FakeCall:
    def __init__(self, data=""):
        self.data = data
        self.message = FakeMessageObj()
        self.from_user = SimpleNamespace(id=1)

    async def answer(self, *a, **k):
        pass


class FakeMessage:
    def __init__(self, *, photo_file_id=None, text=None):
        self.photo = [SimpleNamespace(file_id=photo_file_id)] if photo_file_id else None
        self.text = text
        self.answers = []

    async def answer(self, *a, **k):
        self.answers.append((a, k))


def _make_store(db_session, **kw):
    brand = Brand(name="Acme", slug="acme")
    db_session.add(brand)
    db_session.commit()
    store = Store(name=kw.pop("name", "Branch"), brand_id=brand.id, **kw)
    db_session.add(store)
    db_session.commit()
    return store.id


# ── Phase A: menu image sent on store selection ──────────────────────────────
@pytest.mark.database
@pytest.mark.asyncio
async def test_menu_image_sent_on_select(db_session, monkeypatch):
    store_id = _make_store(db_session, menu_image_file_id="menu_board_42", name="HasImg")

    # Stub the downstream category render so we isolate the image send.
    import bot.handlers.user.shop_and_goods as sg

    async def _noop(call, state):
        return None

    monkeypatch.setattr(sg, "show_brand_categories", _noop)

    from bot.handlers.user.store_selection import _show_categories

    call = FakeCall()
    state = FakeState({"current_store_id": store_id, "current_store_name": "HasImg"})
    await _show_categories(call, state)

    assert call.message.photos == [("menu_board_42", "HasImg")]


@pytest.mark.database
@pytest.mark.asyncio
async def test_no_menu_image_no_photo(db_session, monkeypatch):
    store_id = _make_store(db_session, name="NoImg")  # no menu_image_file_id

    import bot.handlers.user.shop_and_goods as sg

    async def _noop(call, state):
        return None

    monkeypatch.setattr(sg, "show_brand_categories", _noop)

    from bot.handlers.user.store_selection import _show_categories

    call = FakeCall()
    state = FakeState({"current_store_id": store_id, "current_store_name": "NoImg"})
    await _show_categories(call, state)

    assert call.message.photos == []


# ── Admin asset management ───────────────────────────────────────────────────
@pytest.mark.database
@pytest.mark.asyncio
async def test_admin_sets_menu_image(db_session):
    store_id = _make_store(db_session)
    from bot.handlers.admin.store_management import set_menu_image_save

    state = FakeState({"asset_store_id": store_id})
    await set_menu_image_save(FakeMessage(photo_file_id="new_menu_img"), state)

    with Database().session() as s:
        assert s.query(Store).filter_by(id=store_id).one().menu_image_file_id == "new_menu_img"


@pytest.mark.database
@pytest.mark.asyncio
async def test_admin_sets_valid_promptpay_id(db_session):
    store_id = _make_store(db_session)
    from bot.handlers.admin.store_management import set_promptpay_id_save

    state = FakeState({"asset_store_id": store_id})
    msg = FakeMessage(text="0812345678")
    await set_promptpay_id_save(msg, state)

    with Database().session() as s:
        assert s.query(Store).filter_by(id=store_id).one().promptpay_id == "0812345678"


@pytest.mark.database
@pytest.mark.asyncio
async def test_admin_rejects_invalid_promptpay_id(db_session):
    store_id = _make_store(db_session)
    from bot.handlers.admin.store_management import set_promptpay_id_save

    state = FakeState({"asset_store_id": store_id})
    msg = FakeMessage(text="12345")  # not 10 or 13 digits
    await set_promptpay_id_save(msg, state)

    with Database().session() as s:
        assert s.query(Store).filter_by(id=store_id).one().promptpay_id is None
    assert msg.answers  # an error message was sent


@pytest.mark.database
@pytest.mark.asyncio
async def test_admin_clears_promptpay(db_session):
    store_id = _make_store(db_session, promptpay_id="0812345678", promptpay_name="Old")
    from bot.handlers.admin.store_management import set_promptpay_id_save

    state = FakeState({"asset_store_id": store_id})
    await set_promptpay_id_save(FakeMessage(text="-"), state)

    with Database().session() as s:
        store = s.query(Store).filter_by(id=store_id).one()
        assert store.promptpay_id is None
        assert store.promptpay_name is None
