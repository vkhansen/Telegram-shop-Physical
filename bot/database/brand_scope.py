"""Brand-scoped SQLAlchemy query helper (Card 19).

All handler-level DB queries that touch brand-partitioned tables should
go through ``brand_query()`` to enforce brand isolation in multi-bot mode.
When brand_id is None (legacy / no-brand-column tables), the filter is skipped.

Usage:
    with Database().session() as s:
        goods = brand_query(s, Goods, brand_id).filter(Goods.is_active.is_(True)).all()
"""
from __future__ import annotations

from typing import Any, Optional, Type

from sqlalchemy.orm import Session


def brand_query(session: Session, model: Type[Any], brand_id: Optional[int]):
    """Return a query on *model* pre-filtered by brand_id if the model has that column.

    If brand_id is None (single-brand legacy mode) or the model has no brand_id
    column, the filter is not applied — preserving backward compatibility.
    """
    q = session.query(model)
    if brand_id is not None and hasattr(model, "brand_id"):
        q = q.filter(model.brand_id == brand_id)
    return q
