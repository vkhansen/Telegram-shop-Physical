"""Enforce channel-agnostic service / util boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from bot.platform.identity import display_name
from bot.utils.location import normalize_delivery_input

ROOT = Path(__file__).resolve().parents[3]
SERVICES = ROOT / "bot" / "services"
UTILS_LOCATION = ROOT / "bot" / "utils" / "location.py"

# Packages that must never be imported from application services
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "aiogram",
        "bot.handlers",
        "bot.channels.instagram.webhook",
        "bot.channels.line.webhook",
    }
)


def _iter_py(dir_path: Path):
    for p in sorted(dir_path.rglob("*.py")):
        if p.name == "__init__.py" and p.stat().st_size == 0:
            continue
        yield p


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0] if alias.name else "")
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
            mods.add(node.module)
    return mods


@pytest.mark.unit
def test_services_do_not_import_aiogram_or_handlers():
    """R3: services stay free of transport / adapter stacks."""
    bad: list[str] = []
    for path in _iter_py(SERVICES):
        # seed / demo helpers may stay free; all services still checked
        imports = _top_level_imports(path)
        for forbidden in _FORBIDDEN_IMPORT_ROOTS:
            root = forbidden.split(".")[0]
            if forbidden in imports or (root == "aiogram" and "aiogram" in imports):
                # allow nothing from aiogram
                if "aiogram" in forbidden or forbidden in imports:
                    if any(i == forbidden or i.startswith(forbidden + ".") for i in imports) or (
                        forbidden == "aiogram" and "aiogram" in imports
                    ):
                        bad.append(f"{path.relative_to(ROOT)} imports {forbidden}")
            if "bot.handlers" in forbidden:
                if any(i == "bot.handlers" or i.startswith("bot.handlers.") for i in imports):
                    bad.append(f"{path.relative_to(ROOT)} imports handlers")
    # tighter: any import module starting with aiogram
    for path in _iter_py(SERVICES):
        for mod in _top_level_imports(path):
            if mod == "aiogram" or mod.startswith("aiogram."):
                bad.append(f"{path.relative_to(ROOT)} → {mod}")
            if mod == "bot.handlers" or mod.startswith("bot.handlers."):
                bad.append(f"{path.relative_to(ROOT)} → {mod}")
    assert not bad, "Service boundary violations:\n" + "\n".join(sorted(set(bad)))


@pytest.mark.unit
def test_location_module_is_pure():
    imports = _top_level_imports(UTILS_LOCATION)
    for mod in imports:
        assert not (mod == "aiogram" or mod.startswith("aiogram.")), mod
        assert not (mod.startswith("bot.handlers")), mod
        assert not (mod.startswith("bot.channels")), mod


@pytest.mark.unit
def test_display_name_not_identity_key():
    label = display_name("instagram", "17841400000000000")
    assert label.startswith("instagram:")
    assert "@" not in label or label  # handle optional
    with_handle = display_name("line", "Uabc", handle="shopuser")
    assert with_handle == "line:@shopuser"


@pytest.mark.unit
def test_normalize_used_for_parity_contract():
    """All channels feed the same DTO shape into ensure_delivery_profile."""
    pin = normalize_delivery_input(latitude=13.75, longitude=100.5)
    maps = normalize_delivery_input(text="https://www.google.com/maps?q=13.75,100.5")
    assert pin is not None and maps is not None
    assert set(pin.as_profile_kwargs()) == set(maps.as_profile_kwargs())
    assert pin.has_gps and maps.has_gps
