"""Pydantic action schemas for Grok AI admin assistant (Card 17).

Every action the AI can take is defined as a strict Pydantic model.
If validation fails, the action is rejected and the AI must ask for corrections.
"""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Menu Mutation Schemas ─────────────────────────────────────────────

class CreateItemAction(BaseModel):
    """Add a new menu item."""
    action: Literal["create_item"] = "create_item"
    item_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    price: Decimal = Field(..., gt=0, le=99999, decimal_places=2)
    category_name: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0, le=99999)
    item_type: Literal["prepared", "product"] = "prepared"

    @field_validator("price")
    @classmethod
    def price_reasonable(cls, v):
        if v > 10000:
            raise ValueError("Price exceeds 10,000 — confirm with admin")
        return v


class UpdateItemAction(BaseModel):
    """Update an existing menu item. Only provided fields are changed."""
    action: Literal["update_item"] = "update_item"
    item_name: str = Field(..., min_length=1, max_length=100)
    new_name: Optional[str] = Field(None, min_length=1, max_length=100)
    new_description: Optional[str] = Field(None, max_length=500)
    new_price: Optional[Decimal] = Field(None, gt=0, le=99999)
    new_category: Optional[str] = Field(None, max_length=100)

    @field_validator("new_price")
    @classmethod
    def price_reasonable(cls, v):
        if v is not None and v > 10000:
            raise ValueError("Price exceeds 10,000 — confirm with admin")
        return v


class DeleteItemAction(BaseModel):
    """Delete a menu item. Requires explicit confirmation."""
    action: Literal["delete_item"] = "delete_item"
    item_name: str = Field(..., min_length=1, max_length=100)
    confirm: bool = Field(..., description="Must be True to proceed")


class BulkPriceUpdateEntry(BaseModel):
    """A single item price update within a bulk operation."""
    item_name: str = Field(..., min_length=1, max_length=100)
    new_price: Decimal = Field(..., gt=0, le=99999)

    @field_validator("new_price")
    @classmethod
    def price_reasonable(cls, v):
        if v > 10000:
            raise ValueError(f"Price {v} exceeds 10,000 — confirm with admin")
        return v


class BulkPriceUpdateAction(BaseModel):
    """Change prices for multiple items at once."""
    action: Literal["bulk_price_update"] = "bulk_price_update"
    updates: list[BulkPriceUpdateEntry] = Field(
        ..., min_length=1, max_length=50,
        description="List of {item_name, new_price} entries"
    )


class CreateCategoryAction(BaseModel):
    """Create a new menu category."""
    action: Literal["create_category"] = "create_category"
    category_name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = Field(default=0, ge=0, le=999)


class DeleteCategoryAction(BaseModel):
    """Delete a menu category. Requires explicit confirmation."""
    action: Literal["delete_category"] = "delete_category"
    category_name: str = Field(..., min_length=1, max_length=100)
    confirm: bool = Field(..., description="Must be True to proceed")


class AdjustStockAction(BaseModel):
    """Adjust inventory stock for an item."""
    action: Literal["adjust_stock"] = "adjust_stock"
    item_name: str = Field(..., min_length=1, max_length=100)
    operation: Literal["set", "add", "remove"]
    quantity: int = Field(..., ge=0, le=99999)
    comment: Optional[str] = Field(None, max_length=200)


# ── Query / Search Schemas ────────────────────────────────────────────

class SearchOrdersAction(BaseModel):
    """Search orders by various filters."""
    action: Literal["search_orders"] = "search_orders"
    order_code: Optional[str] = Field(None, max_length=6)
    buyer_id: Optional[int] = None
    status: Optional[Literal[
        "pending", "reserved", "confirmed", "preparing",
        "ready", "out_for_delivery", "delivered",
        "cancelled", "expired"
    ]] = None
    payment_method: Optional[Literal["bitcoin", "cash", "promptpay"]] = None
    delivery_type: Optional[Literal["door", "dead_drop", "pickup"]] = None
    date_from: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    date_to: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(default=20, ge=1, le=100)


class SearchChatMessagesAction(BaseModel):
    """Search delivery chat messages."""
    action: Literal["search_chat"] = "search_chat"
    order_id: Optional[int] = None
    order_code: Optional[str] = None
    sender_role: Optional[Literal["driver", "customer"]] = None
    keyword: Optional[str] = Field(None, max_length=100)
    has_photo: Optional[bool] = None
    has_location: Optional[bool] = None
    date_from: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    date_to: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(default=20, ge=1, le=100)


class SearchDeliveriesAction(BaseModel):
    """Search delivery data — zones, GPS, photos, proof."""
    action: Literal["search_deliveries"] = "search_deliveries"
    delivery_zone: Optional[str] = None
    has_delivery_photo: Optional[bool] = None
    has_gps: Optional[bool] = None
    driver_id: Optional[int] = None
    delivery_type: Optional[Literal["door", "dead_drop", "pickup"]] = None
    date_from: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    date_to: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(default=20, ge=1, le=100)


class LookupUserAction(BaseModel):
    """Look up a user profile, their orders, referrals, spending."""
    action: Literal["lookup_user"] = "lookup_user"
    telegram_id: Optional[int] = None
    phone_number: Optional[str] = Field(None, max_length=50)
    include_orders: bool = Field(default=False)
    include_referrals: bool = Field(default=False)

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.telegram_id and not self.phone_number:
            raise ValueError("Provide at least telegram_id or phone_number")
        return self


class GetStatsAction(BaseModel):
    """Get shop statistics for a date range."""
    action: Literal["get_stats"] = "get_stats"
    date_from: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    date_to: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    include_revenue: bool = True
    include_top_items: bool = False
    include_user_growth: bool = False


class ViewInventoryAction(BaseModel):
    """View current inventory status."""
    action: Literal["view_inventory"] = "view_inventory"
    category_filter: Optional[str] = None
    only_low_stock: bool = False
    low_stock_threshold: int = Field(default=5, ge=0)


# ── Data Import Schemas ───────────────────────────────────────────────

class MenuImportRow(BaseModel):
    """Single row of imported menu data — validated per-item."""
    item_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: Decimal = Field(..., gt=0, le=99999)
    category_name: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0, le=99999)
    item_type: Literal["prepared", "product"] = "prepared"


class MenuImportAction(BaseModel):
    """Bulk import menu items from parsed data."""
    action: Literal["import_menu"] = "import_menu"
    items: list[MenuImportRow] = Field(..., min_length=1, max_length=500)
    create_missing_categories: bool = Field(default=True)
    skip_existing: bool = Field(
        default=True,
        description="Skip items that already exist instead of overwriting"
    )
    overwrite_existing: bool = Field(default=False)


class ColumnMappingGuess(BaseModel):
    """Grok's best guess at mapping CSV columns to menu fields."""
    source_column: str
    target_field: Literal[
        "item_name", "description", "price",
        "category_name", "stock_quantity",
        "skip"
    ]
    confidence: float = Field(ge=0, le=1)
    sample_values: list[str] = Field(default_factory=list, max_length=3)


class DataMappingProposal(BaseModel):
    """Grok proposes how to map incoming data columns to menu schema."""
    action: Literal["propose_mapping"] = "propose_mapping"
    mappings: list[ColumnMappingGuess]
    unmapped_required: list[str] = Field(
        default_factory=list,
        description="Required fields with no matching column — must ask admin"
    )
    warnings: list[str] = Field(default_factory=list)


# ── Schema Registry ──────────────────────────────────────────────────

TOOL_SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "create_item": CreateItemAction,
    "update_item": UpdateItemAction,
    "delete_item": DeleteItemAction,
    "bulk_price_update": BulkPriceUpdateAction,
    "create_category": CreateCategoryAction,
    "delete_category": DeleteCategoryAction,
    "adjust_stock": AdjustStockAction,
    "search_orders": SearchOrdersAction,
    "search_chat": SearchChatMessagesAction,
    "search_deliveries": SearchDeliveriesAction,
    "lookup_user": LookupUserAction,
    "get_stats": GetStatsAction,
    "view_inventory": ViewInventoryAction,
    "import_menu": MenuImportAction,
    "propose_mapping": DataMappingProposal,
}

READ_TOOLS = {
    "search_orders", "search_chat", "search_deliveries",
    "lookup_user", "get_stats", "view_inventory", "propose_mapping",
}

MUTATION_TOOLS = {
    "create_item", "update_item", "delete_item",
    "bulk_price_update", "adjust_stock",
    "create_category", "delete_category", "import_menu",
}
