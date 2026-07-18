"""Channel-agnostic location normalization (platform abstraction)."""

from __future__ import annotations

import pytest

from bot.utils.location import (
    build_maps_link,
    extract_coords_from_text,
    extract_coords_from_url,
    looks_like_maps_url,
    normalize_delivery_input,
)


@pytest.mark.unit
class TestExtractCoords:
    def test_maps_q_param(self):
        coords = extract_coords_from_url("https://www.google.com/maps?q=13.7563,100.5018")
        assert coords is not None
        lat, lng = coords
        assert abs(lat - 13.7563) < 1e-6
        assert abs(lng - 100.5018) < 1e-6

    def test_maps_at_path(self):
        coords = extract_coords_from_url(
            "https://www.google.com/maps/place/Foo/@13.75,100.50,17z"
        )
        assert coords is not None
        assert abs(coords[0] - 13.75) < 1e-6

    def test_out_of_range(self):
        assert extract_coords_from_url("https://maps.google.com/?q=91.0,100.0") is None

    def test_bare_coords(self):
        c = extract_coords_from_text("13.7563, 100.5018")
        assert c is not None
        assert abs(c[0] - 13.7563) < 1e-6
        assert abs(c[1] - 100.5018) < 1e-6

    def test_bare_semicolon(self):
        c = extract_coords_from_text("13.75;100.50")
        assert c is not None
        assert abs(c[0] - 13.75) < 1e-6

    def test_non_maps_none(self):
        assert extract_coords_from_url("just a regular address 123") is None
        assert extract_coords_from_text("") is None


@pytest.mark.unit
class TestNormalize:
    def test_explicit_gps(self):
        loc = normalize_delivery_input(latitude=13.7563, longitude=100.5018)
        assert loc is not None
        assert loc.has_gps
        assert loc.source == "explicit"
        assert "13.7563" in (loc.google_maps_link or "")

    def test_maps_url_field(self):
        loc = normalize_delivery_input(
            maps_url="https://www.google.com/maps?q=13.7563,100.5018",
            landmark="Near BTS",
        )
        assert loc is not None
        assert loc.has_gps
        assert loc.delivery_address == "Near BTS"

    def test_text_maps_paste(self):
        loc = normalize_delivery_input(
            text="https://www.google.com/maps?q=13.7563,100.5018"
        )
        assert loc is not None
        assert loc.has_gps

    def test_free_text_no_gps(self):
        loc = normalize_delivery_input(text="Soi 11 Sukhumvit Bangkok")
        assert loc is not None
        assert not loc.has_gps
        assert loc.source == "free_text"

    def test_too_short_none(self):
        assert normalize_delivery_input(text="ab") is None

    def test_build_maps_link(self):
        assert build_maps_link(1.0, 2.0) == "https://www.google.com/maps?q=1.0,2.0"
        assert build_maps_link(None, 1.0) is None

    def test_looks_like_maps(self):
        assert looks_like_maps_url("https://maps.app.goo.gl/abc")
        assert not looks_like_maps_url("Sukhumvit Road")

    def test_as_profile_kwargs(self):
        loc = normalize_delivery_input(latitude=13.0, longitude=100.0)
        assert loc is not None
        kw = loc.as_profile_kwargs()
        assert kw["latitude"] == 13.0
        assert "delivery_address" in kw
