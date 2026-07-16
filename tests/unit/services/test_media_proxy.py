"""CARD-38 Phase B — media proxy allowlist + URL helpers."""

from decimal import Decimal

import pytest

from bot.database.models.main import Brand, Categories, Goods, Store
from bot.services.media_proxy import (
    _encode_token,
    is_catalog_file_id,
    media_url_for,
    resolve_file_id_from_token,
)


@pytest.fixture
def catalog_media(db_engine):
    from bot.database.main import Database

    with Database().session() as s:
        b = Brand(name="Media Brand", slug="media-brand", logo_file_id="logo_fid_abc")
        s.add(b)
        s.flush()
        st = Store(
            name="Main",
            slug="main",
            brand_id=b.id,
            menu_image_file_id="menu_fid_xyz",
            is_active=True,
        )
        s.add(st)
        s.add(Categories(name="M", brand_id=b.id, image_file_id="cat_fid"))
        s.flush()
        g = Goods(
            name="Item One",
            price=Decimal("10"),
            description="d",
            category_name="M",
            brand_id=b.id,
            image_file_id="item_fid_123",
            item_type="prepared",
        )
        s.add(g)
        s.commit()
        return {"brand_id": b.id, "logo": "logo_fid_abc", "item": "item_fid_123", "private": "slip_secret_fid"}


def test_media_url_contains_media_path(catalog_media):
    url = media_url_for(catalog_media["item"], brand_id=catalog_media["brand_id"])
    assert url is not None
    assert "/media/" in url
    assert f"-b{catalog_media['brand_id']}" in url


def test_allowlist_catalog_only(catalog_media):
    assert is_catalog_file_id(catalog_media["logo"], catalog_media["brand_id"]) is True
    assert is_catalog_file_id(catalog_media["item"], catalog_media["brand_id"]) is True
    assert is_catalog_file_id(catalog_media["private"], catalog_media["brand_id"]) is False


def test_resolve_token_roundtrip(catalog_media):
    token = _encode_token(catalog_media["item"], catalog_media["brand_id"])
    fid, bid = resolve_file_id_from_token(token)
    assert fid == catalog_media["item"]
    assert bid == catalog_media["brand_id"]


def test_catalog_dto_uses_media_url(catalog_media):
    from bot.services.catalog_public import get_brand_public

    data = get_brand_public("media-brand")
    assert data is not None
    assert data["logo_url"] is not None
    assert "/media/" in data["logo_url"]
    assert "telegram-file:" not in data["logo_url"]
