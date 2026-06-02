"""Data-integrity validation for the brand / store / menu graph.

The schema allows several "valid SQL, invalid business config" states that no
single foreign key can catch — most importantly:

  * nullable ``brand_id`` columns (a store/category/item with no brand = orphan),
  * a menu item whose ``brand_id`` differs from its category's ``brand_id``
    (cross-brand leak — categories.name is a *global* PK, so this is possible),
  * a brand with zero or more-than-one default store,
  * branch inventory pointing at an item from a different brand,
  * reserved > stock, non-positive prices, etc.

``check_integrity(session)`` runs every check and returns a flat list of
:class:`Violation`. It performs only reads and works identically on SQLite
(tests) and PostgreSQL (production). Use it from the CLI (``validate-data``),
from preflight at startup, and from the fuzz seeder to prove generated data is
clean.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List

from sqlalchemy.orm import Session

from bot.database.models.main import (
    Brand,
    BrandStaff,
    BotConfig,
    BranchInventory,
    Categories,
    Goods,
    Store,
)


class Severity(str, Enum):
    ERROR = "error"      # broken config — must be fixed
    WARNING = "warning"  # suspicious / legacy — worth a look


@dataclass(frozen=True)
class Violation:
    check: str
    severity: Severity
    entity: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper():7}] {self.check}: {entity_msg(self)}"


def entity_msg(v: "Violation") -> str:
    return f"{v.entity} — {v.detail}"


# --------------------------------------------------------------------------- #
# Individual checks. Each takes a Session and returns a list of Violation.
# --------------------------------------------------------------------------- #

def _brand_ids(session: Session) -> set[int]:
    return {bid for (bid,) in session.query(Brand.id).all()}


def check_brand_references(session: Session) -> List[Violation]:
    """Every non-null brand_id on a structural row must point at a real brand."""
    out: List[Violation] = []
    brands = _brand_ids(session)
    for model, label, key in (
        (Store, "store", "name"),
        (Categories, "category", "name"),
        (Goods, "item", "name"),
        (BrandStaff, "brand_staff", "id"),
        (BotConfig, "bot_config", "id"),
    ):
        for row in session.query(model).all():
            bid = getattr(row, "brand_id", None)
            if bid is not None and bid not in brands:
                out.append(Violation(
                    "brand_reference", Severity.ERROR,
                    f"{label}={getattr(row, key)!r}",
                    f"brand_id={bid} does not exist",
                ))
    return out


def check_unbranded(session: Session) -> List[Violation]:
    """Structural rows with brand_id IS NULL are orphans (legacy single-brand)."""
    out: List[Violation] = []
    for model, label, key in (
        (Store, "store", "name"),
        (Categories, "category", "name"),
        (Goods, "item", "name"),
    ):
        for row in session.query(model).filter(model.brand_id.is_(None)).all():
            out.append(Violation(
                "unbranded", Severity.WARNING,
                f"{label}={getattr(row, key)!r}",
                "brand_id is NULL (not attached to any brand)",
            ))
    return out


def check_item_category(session: Session) -> List[Violation]:
    """Each item's category must exist and belong to the same brand as the item."""
    out: List[Violation] = []
    cat_brand = {name: bid for (name, bid) in session.query(Categories.name, Categories.brand_id).all()}
    for g in session.query(Goods).all():
        if g.category_name not in cat_brand:
            out.append(Violation(
                "item_category_missing", Severity.ERROR,
                f"item={g.name!r}",
                f"category_name={g.category_name!r} does not exist",
            ))
            continue
        if cat_brand[g.category_name] != g.brand_id:
            out.append(Violation(
                "item_category_cross_brand", Severity.ERROR,
                f"item={g.name!r}",
                f"item brand_id={g.brand_id} but category {g.category_name!r} "
                f"brand_id={cat_brand[g.category_name]}",
            ))
    return out


def check_default_store(session: Session) -> List[Violation]:
    """Each active brand should have exactly one default store."""
    out: List[Violation] = []
    for b in session.query(Brand).filter(Brand.is_active.is_(True)).all():
        defaults = session.query(Store).filter(
            Store.brand_id == b.id, Store.is_default.is_(True)
        ).count()
        total = session.query(Store).filter(Store.brand_id == b.id).count()
        if total == 0:
            out.append(Violation("brand_no_store", Severity.WARNING,
                                 f"brand={b.slug!r}", "active brand has no stores"))
        elif defaults == 0:
            out.append(Violation("brand_no_default_store", Severity.WARNING,
                                 f"brand={b.slug!r}", "no store marked is_default"))
        elif defaults > 1:
            out.append(Violation("brand_multiple_default_stores", Severity.ERROR,
                                 f"brand={b.slug!r}", f"{defaults} stores marked is_default (must be 1)"))
    return out


def check_bot_config(session: Session) -> List[Violation]:
    """Each active brand should have a bot config (multi-bot runtime needs it)."""
    out: List[Violation] = []
    configured = {bid for (bid,) in session.query(BotConfig.brand_id).all()}
    for b in session.query(Brand).filter(Brand.is_active.is_(True)).all():
        if b.id not in configured:
            out.append(Violation("brand_no_bot_config", Severity.WARNING,
                                 f"brand={b.slug!r}", "active brand has no BotConfig"))
    return out


def check_staff_store_brand(session: Session) -> List[Violation]:
    """A staff member scoped to a store must be scoped to that store's brand."""
    out: List[Violation] = []
    store_brand = {sid: bid for (sid, bid) in session.query(Store.id, Store.brand_id).all()}
    for s in session.query(BrandStaff).filter(BrandStaff.store_id.isnot(None)).all():
        if s.store_id not in store_brand:
            out.append(Violation("staff_store_missing", Severity.ERROR,
                                 f"brand_staff={s.id}", f"store_id={s.store_id} does not exist"))
        elif store_brand[s.store_id] != s.brand_id:
            out.append(Violation("staff_store_cross_brand", Severity.ERROR,
                                 f"brand_staff={s.id}",
                                 f"staff brand_id={s.brand_id} but store belongs to brand_id={store_brand[s.store_id]}"))
    return out


def check_branch_inventory(session: Session) -> List[Violation]:
    """Branch inventory must reference a real item of the store's own brand."""
    out: List[Violation] = []
    store_brand = {sid: bid for (sid, bid) in session.query(Store.id, Store.brand_id).all()}
    item_brand = {name: bid for (name, bid) in session.query(Goods.name, Goods.brand_id).all()}
    for bi in session.query(BranchInventory).all():
        if bi.store_id not in store_brand:
            out.append(Violation("branch_inv_store_missing", Severity.ERROR,
                                 f"branch_inventory={bi.id}", f"store_id={bi.store_id} does not exist"))
        if bi.item_name not in item_brand:
            out.append(Violation("branch_inv_item_missing", Severity.ERROR,
                                 f"branch_inventory={bi.id}", f"item_name={bi.item_name!r} does not exist"))
        elif bi.store_id in store_brand and store_brand[bi.store_id] != item_brand[bi.item_name]:
            out.append(Violation("branch_inv_cross_brand", Severity.ERROR,
                                 f"branch_inventory={bi.id}",
                                 f"store brand_id={store_brand[bi.store_id]} but item brand_id={item_brand[bi.item_name]}"))
        if bi.reserved_quantity > bi.stock_quantity:
            out.append(Violation("branch_inv_oversold", Severity.WARNING,
                                 f"branch_inventory={bi.id}",
                                 f"reserved={bi.reserved_quantity} > stock={bi.stock_quantity}"))
        if bi.stock_quantity < 0 or bi.reserved_quantity < 0:
            out.append(Violation("branch_inv_negative", Severity.ERROR,
                                 f"branch_inventory={bi.id}",
                                 f"negative quantity (stock={bi.stock_quantity}, reserved={bi.reserved_quantity})"))
    return out


def check_item_sanity(session: Session) -> List[Violation]:
    """Per-item config sanity: positive price, non-negative / non-oversold stock."""
    out: List[Violation] = []
    for g in session.query(Goods).all():
        if g.price is None or g.price <= 0:
            out.append(Violation("item_bad_price", Severity.ERROR,
                                 f"item={g.name!r}", f"price={g.price} must be > 0"))
        if g.stock_quantity < 0 or g.reserved_quantity < 0:
            out.append(Violation("item_negative_stock", Severity.ERROR,
                                 f"item={g.name!r}",
                                 f"negative (stock={g.stock_quantity}, reserved={g.reserved_quantity})"))
        elif g.is_product and g.reserved_quantity > g.stock_quantity:
            out.append(Violation("item_oversold", Severity.WARNING,
                                 f"item={g.name!r}",
                                 f"reserved={g.reserved_quantity} > stock={g.stock_quantity}"))
    return out


_VALID_ITEM_TYPES = {"prepared", "product"}
_VALID_MODIFIER_TYPES = {"single", "multi"}


def check_item_required_fields(session: Session) -> List[Violation]:
    """Every menu item must carry the fields needed to sell it."""
    out: List[Violation] = []
    for g in session.query(Goods).all():
        if not g.description or not str(g.description).strip():
            out.append(Violation("item_missing_description", Severity.ERROR,
                                 f"item={g.name!r}", "description is empty"))
        if g.category_name is None or not str(g.category_name).strip():
            out.append(Violation("item_missing_category", Severity.ERROR,
                                 f"item={g.name!r}", "category_name is empty"))
        if g.item_type not in _VALID_ITEM_TYPES:
            out.append(Violation("item_bad_type", Severity.ERROR,
                                 f"item={g.name!r}",
                                 f"item_type={g.item_type!r} not in {sorted(_VALID_ITEM_TYPES)}"))
    return out


def check_modifier_schema(session: Session) -> List[Violation]:
    """If an item declares modifiers, the JSON must be a well-formed option spec."""
    out: List[Violation] = []
    for g in session.query(Goods).all():
        mods = g.modifiers
        if mods is None:
            continue
        if not isinstance(mods, dict):
            out.append(Violation("modifier_bad_shape", Severity.ERROR,
                                 f"item={g.name!r}", "modifiers must be a JSON object"))
            continue
        for group_key, group in mods.items():
            where = f"item={g.name!r} group={group_key!r}"
            if not isinstance(group, dict):
                out.append(Violation("modifier_bad_group", Severity.ERROR, where, "group must be an object"))
                continue
            if not group.get("label"):
                out.append(Violation("modifier_missing_label", Severity.ERROR, where, "missing 'label'"))
            if group.get("type") not in _VALID_MODIFIER_TYPES:
                out.append(Violation("modifier_bad_type", Severity.ERROR, where,
                                     f"type={group.get('type')!r} not in {sorted(_VALID_MODIFIER_TYPES)}"))
            options = group.get("options")
            if not isinstance(options, list) or not options:
                out.append(Violation("modifier_no_options", Severity.ERROR, where, "must have a non-empty 'options' list"))
                continue
            seen_ids = set()
            for opt in options:
                if not isinstance(opt, dict) or "id" not in opt or "label" not in opt:
                    out.append(Violation("modifier_bad_option", Severity.ERROR, where,
                                         f"option missing id/label: {opt!r}"))
                    continue
                if not isinstance(opt.get("price", 0), (int, float)):
                    out.append(Violation("modifier_bad_option_price", Severity.ERROR, where,
                                         f"option {opt['id']!r} price must be numeric"))
                if opt["id"] in seen_ids:
                    out.append(Violation("modifier_duplicate_option", Severity.ERROR, where,
                                         f"duplicate option id {opt['id']!r}"))
                seen_ids.add(opt["id"])
    return out


def check_empty_categories(session: Session) -> List[Violation]:
    """A category with no items is a dead menu section."""
    out: List[Violation] = []
    used = {name for (name,) in session.query(Goods.category_name).distinct().all()}
    for c in session.query(Categories).all():
        if c.name not in used:
            out.append(Violation("empty_category", Severity.WARNING,
                                 f"category={c.name!r}", "category has no items"))
    return out


CHECKS: tuple[Callable[[Session], List[Violation]], ...] = (
    check_brand_references,
    check_unbranded,
    check_item_category,
    check_default_store,
    check_bot_config,
    check_staff_store_brand,
    check_branch_inventory,
    check_item_sanity,
    check_item_required_fields,
    check_modifier_schema,
    check_empty_categories,
)


def check_integrity(session: Session, *, include_warnings: bool = True) -> List[Violation]:
    """Run all integrity checks and return a flat list of violations."""
    out: List[Violation] = []
    for check in CHECKS:
        out.extend(check(session))
    if not include_warnings:
        out = [v for v in out if v.severity is Severity.ERROR]
    return out


def summarize(violations: List[Violation]) -> dict[str, int]:
    errors = sum(1 for v in violations if v.severity is Severity.ERROR)
    return {"total": len(violations), "errors": errors, "warnings": len(violations) - errors}
