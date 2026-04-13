"""
Tests for bot/utils/menu_io.py — JSON menu export/import + validation.

menu_io is the source of bugs M7 (Decimal→float precision loss on round-trip)
and H8 (photo IndexError on empty media lists). These tests pin current
behavior and guard against regressions in the pure-function paths.
"""
import json
import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.database.models.main import Categories, Goods
from bot.utils import menu_io
from bot.utils.menu_io import (
    DecimalEncoder,
    _safe_filename,
    _strip_file_ids,
    download_menu_images,
    export_menu_to_json,
    import_menu_from_json,
    upload_menu_images,
    validate_menu_json,
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_lowercases_and_replaces_spaces(self):
        assert _safe_filename("Pad Thai") == "pad_thai"

    def test_strips_punctuation(self):
        assert _safe_filename("Mom's Pad Thai!") == "moms_pad_thai"

    def test_collapses_whitespace_and_dashes(self):
        assert _safe_filename("A - B   C") == "a_b_c"

    def test_trims_leading_trailing_underscores(self):
        assert _safe_filename("  hello  ") == "hello"

    def test_length_capped_at_50(self):
        result = _safe_filename("x" * 200)
        assert len(result) == 50
        assert result == "x" * 50

    def test_unicode_letters_preserved(self):
        # \w matches unicode letters but not all combining marks
        # (Thai sara-a U+0E31 is category Mn and gets stripped).
        # We just care that base letters survive.
        result = _safe_filename("ผัดไทย")
        assert "ผ" in result
        assert "ด" in result
        assert "ไ" in result
        assert "ท" in result
        assert "ย" in result

    def test_empty_string(self):
        assert _safe_filename("") == ""

    def test_only_punctuation(self):
        assert _safe_filename("!!!???") == ""


class TestStripFileIds:
    def test_removes_category_image_file_id(self):
        data = {"categories": [{"name": "A", "_image_file_id": "abc"}], "items": []}
        _strip_file_ids(data)
        assert "_image_file_id" not in data["categories"][0]
        assert data["categories"][0]["name"] == "A"

    def test_removes_item_image_and_gallery_file_ids(self):
        data = {
            "categories": [],
            "items": [
                {
                    "name": "X",
                    "_image_file_id": "primary",
                    "gallery": [
                        {"file": "x.jpg", "_file_id": "g1"},
                        {"file": "y.jpg", "_file_id": "g2"},
                    ],
                }
            ],
        }
        _strip_file_ids(data)
        item = data["items"][0]
        assert "_image_file_id" not in item
        for m in item["gallery"]:
            assert "_file_id" not in m
            assert "file" in m

    def test_missing_keys_no_error(self):
        # Items without _image_file_id or gallery should not crash
        data = {"categories": [{"name": "A"}], "items": [{"name": "X"}]}
        _strip_file_ids(data)  # should not raise
        assert data["categories"] == [{"name": "A"}]
        assert data["items"] == [{"name": "X"}]

    def test_empty_top_level_keys(self):
        _strip_file_ids({})  # no categories/items keys
        _strip_file_ids({"categories": [], "items": []})


class TestDecimalEncoder:
    def test_encodes_decimal_as_float(self):
        result = json.dumps({"price": Decimal("12.50")}, cls=DecimalEncoder)
        assert json.loads(result)["price"] == 12.50

    def test_passes_through_other_types(self):
        result = json.dumps({"n": 1, "s": "x"}, cls=DecimalEncoder)
        assert json.loads(result) == {"n": 1, "s": "x"}

    def test_decimal_precision_lost_m7_pinned(self):
        # Pin M7: Decimal→float conversion can lose precision.
        # This test documents the current (lossy) behavior — if the encoder
        # is ever switched to str(obj), update this test too.
        encoded = json.dumps({"p": Decimal("0.1")}, cls=DecimalEncoder)
        assert json.loads(encoded)["p"] == 0.1  # float, not Decimal


# ---------------------------------------------------------------------------
# validate_menu_json
# ---------------------------------------------------------------------------

def _write_json(tmp_path, payload):
    p = tmp_path / "menu.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return str(p)


class TestValidateMenuJson:
    def test_valid_minimal_menu(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "Drinks"}],
            "items": [{"name": "Coke", "category": "Drinks", "price": "1.50"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is True
        assert errors == []

    def test_file_not_found(self, tmp_path):
        ok, errors = validate_menu_json(str(tmp_path / "nope.json"))
        assert ok is False
        assert any("not found" in e.lower() for e in errors)

    def test_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        ok, errors = validate_menu_json(str(p))
        assert ok is False
        assert any("Invalid JSON" in e for e in errors)

    def test_root_must_be_object(self, tmp_path):
        p = tmp_path / "arr.json"
        p.write_text("[]", encoding="utf-8")
        ok, errors = validate_menu_json(str(p))
        assert ok is False
        assert "Root must be a JSON object" in errors

    def test_missing_categories_array(self, tmp_path):
        path = _write_json(tmp_path, {"items": []})
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("categories" in e for e in errors)

    def test_missing_items_array(self, tmp_path):
        path = _write_json(tmp_path, {"categories": []})
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("items" in e for e in errors)

    def test_category_missing_name(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"sort_order": 1}],
            "items": [],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("missing 'name'" in e for e in errors)

    def test_category_not_object(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": ["not a dict"],
            "items": [],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("must be an object" in e for e in errors)

    def test_item_missing_name(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{"category": "A"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("missing 'name'" in e for e in errors)

    def test_item_missing_category(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{"name": "X"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("missing 'category'" in e for e in errors)

    def test_item_references_unknown_category(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{"name": "X", "category": "Nonexistent"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("unknown category" in e for e in errors)

    def test_item_invalid_price(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{"name": "X", "category": "A", "price": "not-a-number"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("invalid price" in e for e in errors)

    def test_item_price_numeric_string_ok(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{"name": "X", "category": "A", "price": "99.99"}],
        })
        ok, errors = validate_menu_json(path)
        assert ok is True

    def test_modifier_group_not_object(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{
                "name": "X", "category": "A",
                "modifiers": {"size": "not-an-object"},
            }],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("must be an object" in e for e in errors)

    def test_modifier_group_missing_options(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{
                "name": "X", "category": "A",
                "modifiers": {"size": {"label": "Size"}},
            }],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("missing 'options'" in e for e in errors)

    def test_modifier_group_valid(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{
                "name": "X", "category": "A",
                "modifiers": {"size": {"options": [{"name": "S"}]}},
            }],
        })
        ok, errors = validate_menu_json(path)
        assert ok is True

    def test_missing_image_files_reported(self, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{
                "name": "X", "category": "A",
                "image": "images/missing.jpg",
                "gallery": [{"file": "images/also_missing.jpg"}],
            }],
        })
        ok, errors = validate_menu_json(path)
        assert ok is False
        assert any("Missing" in e and "image" in e for e in errors)

    def test_present_image_files_ok(self, tmp_path):
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "real.jpg").write_bytes(b"fake")
        path = _write_json(tmp_path, {
            "categories": [{"name": "A"}],
            "items": [{
                "name": "X", "category": "A",
                "image": "images/real.jpg",
            }],
        })
        ok, errors = validate_menu_json(path)
        assert ok is True


# ---------------------------------------------------------------------------
# export_menu_to_json
# ---------------------------------------------------------------------------

class TestExportMenuToJson:
    def test_export_empty_db(self, db_with_roles, tmp_path):
        out = str(tmp_path / "export1")
        result = export_menu_to_json(output_dir=out)
        assert result == out
        assert os.path.isdir(out)
        assert os.path.isdir(os.path.join(out, "images"))

        with open(os.path.join(out, "menu.json"), encoding="utf-8") as f:
            data = json.load(f)
        assert data["version"] == "2.0"
        assert data["categories"] == []
        assert data["items"] == []
        assert data["currency"] == "THB"
        assert "exported_at" in data

    def test_export_with_categories_and_items(self, db_session, tmp_path):
        cat = Categories(name="Drinks", sort_order=1, description="Cold stuff")
        db_session.add(cat)
        db_session.commit()

        item = Goods(
            name="Iced Tea",
            price=Decimal("45.00"),
            description="Refreshing",
            category_name="Drinks",
            stock_quantity=0,
            item_type="prepared",
            prep_time_minutes=3,
            allergens="none",
            is_active=True,
            calories=120,
        )
        db_session.add(item)
        db_session.commit()

        out = str(tmp_path / "export2")
        export_menu_to_json(output_dir=out)

        with open(os.path.join(out, "menu.json"), encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Drinks"
        assert data["categories"][0]["sort_order"] == 1
        assert data["categories"][0]["image"] is None

        assert len(data["items"]) == 1
        exported_item = data["items"][0]
        assert exported_item["name"] == "Iced Tea"
        # Price is stored as string to preserve precision on the way out
        assert exported_item["price"] == "45.00"
        assert exported_item["category"] == "Drinks"
        assert exported_item["calories"] == 120
        assert exported_item["image"] is None
        assert exported_item["gallery"] == []

    def test_export_includes_image_file_id_reference(self, db_session, tmp_path):
        cat = Categories(name="Food", image_file_id="cat_file_abc")
        db_session.add(cat)
        db_session.commit()

        item = Goods(
            name="Burger",
            price=Decimal("100"),
            description="Beef",
            category_name="Food",
            stock_quantity=0,
        )
        item.image_file_id = "item_file_xyz"
        item.media = [
            {"type": "photo", "file_id": "p1"},
            {"type": "video", "file_id": "v1"},
        ]
        db_session.add(item)
        db_session.commit()

        out = str(tmp_path / "export3")
        export_menu_to_json(output_dir=out)

        with open(os.path.join(out, "menu.json"), encoding="utf-8") as f:
            data = json.load(f)

        cat_entry = data["categories"][0]
        assert cat_entry["image"] == "images/cat_food.jpg"
        assert cat_entry["_image_file_id"] == "cat_file_abc"

        item_entry = data["items"][0]
        assert item_entry["image"] == "images/item_burger_main.jpg"
        assert item_entry["_image_file_id"] == "item_file_xyz"
        assert len(item_entry["gallery"]) == 2
        assert item_entry["gallery"][0]["file"].endswith(".jpg")
        assert item_entry["gallery"][1]["file"].endswith(".mp4")
        assert item_entry["gallery"][0]["_file_id"] == "p1"
        assert item_entry["gallery"][1]["_file_id"] == "v1"

    def test_export_default_output_dir(self, db_with_roles, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = export_menu_to_json()  # no arg → timestamped default
        assert result.startswith("menu_export_")
        assert os.path.isdir(result)


# ---------------------------------------------------------------------------
# import_menu_from_json
# ---------------------------------------------------------------------------

class TestImportMenuFromJson:
    def test_import_creates_new_categories_and_items(self, db_session, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "Drinks", "sort_order": 2}],
            "items": [{
                "name": "Soda",
                "price": "25.00",
                "description": "Fizzy",
                "category": "Drinks",
                "stock_quantity": 10,
            }],
        })
        stats = import_menu_from_json(path)
        assert stats["categories_created"] == 1
        assert stats["items_created"] == 1
        assert stats["errors"] == []

        # Verify via a fresh session
        from bot.database.main import Database
        with Database().session() as s:
            assert s.query(Categories).filter_by(name="Drinks").first() is not None
            g = s.query(Goods).filter_by(name="Soda").first()
            assert g is not None
            assert g.category_name == "Drinks"

    def test_import_updates_existing(self, db_session, tmp_path):
        db_session.add(Categories(name="Drinks", sort_order=1, description="old"))
        db_session.commit()
        db_session.add(Goods(
            name="Soda", price=Decimal("10"), description="old-desc",
            category_name="Drinks", stock_quantity=5,
        ))
        db_session.commit()

        path = _write_json(tmp_path, {
            "categories": [{"name": "Drinks", "sort_order": 9, "description": "new"}],
            "items": [{
                "name": "Soda",
                "price": "99.00",
                "description": "new-desc",
                "category": "Drinks",
            }],
        })
        stats = import_menu_from_json(path)
        assert stats["categories_updated"] == 1
        assert stats["items_updated"] == 1
        assert stats["categories_created"] == 0
        assert stats["items_created"] == 0

        db_session.expire_all()
        cat = db_session.query(Categories).filter_by(name="Drinks").one()
        assert cat.sort_order == 9
        assert cat.description == "new"
        item = db_session.query(Goods).filter_by(name="Soda").one()
        assert str(item.price) == "99.00"
        assert item.description == "new-desc"

    def test_import_skips_item_with_unknown_category(self, db_session, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "Drinks"}],
            "items": [{
                "name": "Ghost", "price": "1", "description": "d",
                "category": "Nonexistent",
            }],
        })
        stats = import_menu_from_json(path)
        assert stats["items_skipped"] == 1
        assert stats["items_created"] == 0
        assert any("category 'Nonexistent' not found" in e for e in stats["errors"])

    def test_import_replace_mode_deletes_existing(self, db_session, tmp_path):
        db_session.add(Categories(name="Old"))
        db_session.commit()
        db_session.add(Goods(
            name="OldItem", price=Decimal("1"), description="d",
            category_name="Old", stock_quantity=0,
        ))
        db_session.commit()

        path = _write_json(tmp_path, {
            "categories": [{"name": "New"}],
            "items": [{
                "name": "NewItem", "price": "2", "description": "n",
                "category": "New",
            }],
        })
        stats = import_menu_from_json(path, mode="replace")
        assert stats["errors"] == []

        db_session.expire_all()
        assert db_session.query(Categories).filter_by(name="Old").first() is None
        assert db_session.query(Goods).filter_by(name="OldItem").first() is None
        assert db_session.query(Categories).filter_by(name="New").first() is not None
        assert db_session.query(Goods).filter_by(name="NewItem").first() is not None

    def test_import_applies_default_stock_to_new_items(self, db_session, tmp_path):
        path = _write_json(tmp_path, {
            "categories": [{"name": "C"}],
            "items": [{
                "name": "NoStockItem", "price": "1", "description": "d",
                "category": "C",
            }],
        })
        import_menu_from_json(path, default_stock=77)
        db_session.expire_all()
        item = db_session.query(Goods).filter_by(name="NoStockItem").one()
        assert item.stock_quantity == 77

    def test_import_with_modifiers(self, db_session, tmp_path):
        mods = {"size": {"options": [{"name": "S", "price_delta": 0}]}}
        path = _write_json(tmp_path, {
            "categories": [{"name": "C"}],
            "items": [{
                "name": "Modded", "price": "5", "description": "d",
                "category": "C", "modifiers": mods,
            }],
        })
        import_menu_from_json(path)
        db_session.expire_all()
        item = db_session.query(Goods).filter_by(name="Modded").one()
        assert item.modifiers == mods

    def test_import_round_trip(self, db_session, tmp_path):
        # Export→import should preserve structural fields
        db_session.add(Categories(name="RT", sort_order=3, description="round-trip"))
        db_session.commit()
        db_session.add(Goods(
            name="RTItem", price=Decimal("12.50"), description="rt",
            category_name="RT", stock_quantity=0, is_active=True,
            prep_time_minutes=5, calories=200,
        ))
        db_session.commit()

        out = str(tmp_path / "rt")
        export_menu_to_json(output_dir=out)
        stats = import_menu_from_json(os.path.join(out, "menu.json"))
        assert stats["errors"] == []
        # Items and categories already existed → updated, not created
        assert stats["categories_updated"] == 1
        assert stats["items_updated"] == 1


# ---------------------------------------------------------------------------
# download_menu_images / upload_menu_images (async, mocked bot)
# ---------------------------------------------------------------------------

class TestDownloadMenuImages:
    @pytest.mark.asyncio
    async def test_download_strips_file_ids_from_json(self, tmp_path):
        export_dir = tmp_path / "exp"
        export_dir.mkdir()
        (export_dir / "images").mkdir()
        payload = {
            "categories": [{
                "name": "C", "image": "images/cat.jpg", "_image_file_id": "cat_fid",
            }],
            "items": [{
                "name": "I", "image": "images/item.jpg", "_image_file_id": "item_fid",
                "gallery": [{"file": "images/g0.jpg", "_file_id": "g_fid", "type": "photo"}],
            }],
        }
        json_path = export_dir / "menu.json"
        json_path.write_text(json.dumps(payload), encoding="utf-8")

        bot = MagicMock()
        bot.get_file = AsyncMock(return_value=MagicMock(file_path="tg/path.jpg"))
        bot.download_file = AsyncMock()

        count = await download_menu_images(bot, str(export_dir))
        assert count == 3
        assert bot.get_file.await_count == 3
        assert bot.download_file.await_count == 3

        # Re-read the stripped JSON
        stripped = json.loads(json_path.read_text(encoding="utf-8"))
        assert "_image_file_id" not in stripped["categories"][0]
        assert "_image_file_id" not in stripped["items"][0]
        assert "_file_id" not in stripped["items"][0]["gallery"][0]

    @pytest.mark.asyncio
    async def test_download_skips_entries_without_file_id(self, tmp_path):
        export_dir = tmp_path / "exp"
        export_dir.mkdir()
        (export_dir / "images").mkdir()
        payload = {
            "categories": [{"name": "NoImg"}],  # no image
            "items": [{"name": "AlsoNoImg"}],
        }
        (export_dir / "menu.json").write_text(json.dumps(payload), encoding="utf-8")

        bot = MagicMock()
        bot.get_file = AsyncMock()
        bot.download_file = AsyncMock()

        count = await download_menu_images(bot, str(export_dir))
        assert count == 0
        bot.get_file.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_download_catches_per_file_errors(self, tmp_path):
        export_dir = tmp_path / "exp"
        export_dir.mkdir()
        (export_dir / "images").mkdir()
        payload = {
            "categories": [{
                "name": "C", "image": "images/cat.jpg", "_image_file_id": "fid",
            }],
            "items": [],
        }
        (export_dir / "menu.json").write_text(json.dumps(payload), encoding="utf-8")

        bot = MagicMock()
        bot.get_file = AsyncMock(side_effect=RuntimeError("telegram down"))
        bot.download_file = AsyncMock()

        count = await download_menu_images(bot, str(export_dir))
        assert count == 0  # failure counted but not raised


class TestUploadMenuImages:
    @pytest.mark.asyncio
    async def test_upload_updates_db_file_ids(self, db_session, tmp_path):
        db_session.add(Categories(name="C"))
        db_session.commit()
        db_session.add(Goods(
            name="I", price=Decimal("1"), description="d",
            category_name="C", stock_quantity=0,
        ))
        db_session.commit()

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "cat.jpg").write_bytes(b"x")
        (images_dir / "item.jpg").write_bytes(b"y")
        (images_dir / "g0.jpg").write_bytes(b"z")

        json_path = tmp_path / "menu.json"
        json_path.write_text(json.dumps({
            "categories": [{"name": "C", "image": "images/cat.jpg"}],
            "items": [{
                "name": "I", "image": "images/item.jpg",
                "gallery": [{"file": "images/g0.jpg", "type": "photo"}],
            }],
        }), encoding="utf-8")

        photo_msg = MagicMock()
        photo_msg.photo = [MagicMock(file_id="new_cat"), MagicMock(file_id="new_cat_big")]
        photo_msg.message_id = 10

        item_msg = MagicMock()
        item_msg.photo = [MagicMock(file_id="new_item_small"), MagicMock(file_id="new_item")]
        item_msg.message_id = 11

        gallery_msg = MagicMock()
        gallery_msg.photo = [MagicMock(file_id="new_g0_small"), MagicMock(file_id="new_g0")]
        gallery_msg.message_id = 12

        bot = MagicMock()
        bot.send_photo = AsyncMock(side_effect=[photo_msg, item_msg, gallery_msg])
        bot.send_video = AsyncMock()
        bot.delete_message = AsyncMock()

        count = await upload_menu_images(bot, str(json_path), chat_id=999)
        assert count == 3

        db_session.expire_all()
        cat = db_session.query(Categories).filter_by(name="C").one()
        item = db_session.query(Goods).filter_by(name="I").one()
        assert cat.image_file_id == "new_cat_big"  # photo[-1]
        assert item.image_file_id == "new_item"
        assert item.media == [{"file_id": "new_g0", "type": "photo"}]

    @pytest.mark.asyncio
    async def test_upload_video_uses_send_video(self, db_session, tmp_path):
        db_session.add(Categories(name="C"))
        db_session.commit()
        db_session.add(Goods(
            name="I", price=Decimal("1"), description="d",
            category_name="C", stock_quantity=0,
        ))
        db_session.commit()

        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "v.mp4").write_bytes(b"v")
        json_path = tmp_path / "menu.json"
        json_path.write_text(json.dumps({
            "categories": [],
            "items": [{
                "name": "I",
                "gallery": [{"file": "images/v.mp4", "type": "video"}],
            }],
        }), encoding="utf-8")

        video_msg = MagicMock()
        video_msg.video = MagicMock(file_id="vid_fid")
        video_msg.message_id = 20

        bot = MagicMock()
        bot.send_photo = AsyncMock()
        bot.send_video = AsyncMock(return_value=video_msg)
        bot.delete_message = AsyncMock()

        count = await upload_menu_images(bot, str(json_path), chat_id=1)
        assert count == 1
        bot.send_video.assert_awaited_once()
        db_session.expire_all()
        item = db_session.query(Goods).filter_by(name="I").one()
        assert item.media == [{"file_id": "vid_fid", "type": "video"}]

    @pytest.mark.asyncio
    async def test_upload_skips_missing_files(self, db_session, tmp_path):
        db_session.add(Categories(name="C"))
        db_session.commit()

        json_path = tmp_path / "menu.json"
        json_path.write_text(json.dumps({
            "categories": [{"name": "C", "image": "images/does_not_exist.jpg"}],
            "items": [],
        }), encoding="utf-8")

        bot = MagicMock()
        bot.send_photo = AsyncMock()
        bot.send_video = AsyncMock()
        bot.delete_message = AsyncMock()

        count = await upload_menu_images(bot, str(json_path), chat_id=1)
        assert count == 0
        bot.send_photo.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_upload_survives_delete_message_failure(self, db_session, tmp_path):
        db_session.add(Categories(name="C"))
        db_session.commit()

        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "cat.jpg").write_bytes(b"x")
        json_path = tmp_path / "menu.json"
        json_path.write_text(json.dumps({
            "categories": [{"name": "C", "image": "images/cat.jpg"}],
            "items": [],
        }), encoding="utf-8")

        photo_msg = MagicMock()
        photo_msg.photo = [MagicMock(file_id="f")]
        photo_msg.message_id = 1

        bot = MagicMock()
        bot.send_photo = AsyncMock(return_value=photo_msg)
        bot.send_video = AsyncMock()
        bot.delete_message = AsyncMock(side_effect=RuntimeError("can't delete"))

        count = await upload_menu_images(bot, str(json_path), chat_id=1)
        assert count == 1  # delete failure is swallowed
