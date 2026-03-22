"""Tests for multi-format data parser (Card 17)."""

from unittest.mock import MagicMock

import pytest

from bot.ai.data_parser import _parse_csv_to_text, _parse_json_to_text, extract_content


class TestParseCsvToText:
    def test_basic_csv(self):
        csv_bytes = b"name,price,category\nPad Thai,150,Noodles\nSom Tam,80,Salads\n"
        result = _parse_csv_to_text(csv_bytes)
        assert "2 rows" in result
        assert "Pad Thai" in result

    def test_utf8_bom(self):
        result = _parse_csv_to_text(b"\xef\xbb\xbfname,price\nTest,100\n")
        assert "1 rows" in result

    def test_empty_csv(self):
        result = _parse_csv_to_text(b"")
        assert "empty" in result.lower() or "no headers" in result.lower()

    def test_many_rows_shows_preview(self):
        lines = ["name,price"] + [f"Item{i},{i*10}" for i in range(20)]
        result = _parse_csv_to_text("\n".join(lines).encode())
        assert "First 5 rows" in result
        assert "15 more rows" in result


class TestParseJsonToText:
    def test_basic_json(self):
        result = _parse_json_to_text(b'[{"name": "Pad Thai", "price": 150}]')
        assert "Pad Thai" in result

    def test_invalid_json(self):
        result = _parse_json_to_text(b"not json")
        assert "Error" in result


class TestExtractContent:
    @pytest.mark.asyncio
    async def test_plain_text(self):
        msg = MagicMock()
        msg.text = "Change pad thai price to 200"
        msg.document = None
        msg.photo = None
        assert await extract_content(msg) == "Change pad thai price to 200"

    @pytest.mark.asyncio
    async def test_photo(self):
        msg = MagicMock()
        msg.text = None
        msg.document = None
        msg.photo = [MagicMock()]
        msg.caption = "Menu photo"
        result = await extract_content(msg)
        assert "photo" in result.lower()

    @pytest.mark.asyncio
    async def test_empty(self):
        msg = MagicMock()
        msg.text = None
        msg.document = None
        msg.photo = None
        assert "Empty" in await extract_content(msg)
