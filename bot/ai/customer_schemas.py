"""Pydantic schemas for all 10 customer Grok assistant tools (Card 22)."""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BrowseMenuAction(BaseModel):
    """Search the menu by keyword, category, dietary tag, or price range. Returns matching items with prices and availability."""
    action: Literal["browse_menu"] = "browse_menu"
    keyword: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    max_price: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    in_stock_only: bool = True
    limit: int = Field(default=10, ge=1, le=20)


class GetTodaySpecialsAction(BaseModel):
    """Return items whose availability window is currently active (Bangkok time). Shows what can be ordered right now."""
    action: Literal["get_today_specials"] = "get_today_specials"
    category: Optional[str] = Field(default=None, max_length=100)


class FindDealsAction(BaseModel):
    """Return currently active public coupon codes with discount details and minimum order conditions."""
    action: Literal["find_deals"] = "find_deals"
    min_order_max: Optional[Decimal] = Field(default=None, description="Only show coupons requiring at most this minimum order amount")


class FindNearbyStoresAction(BaseModel):
    """Find stores near the customer's location, sorted by distance with delivery availability."""
    action: Literal["find_nearby_stores"] = "find_nearby_stores"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: float = Field(default=10.0, gt=0, le=50)


class CheckCouponAction(BaseModel):
    """Validate a coupon code: check if it is active, not expired, and calculate the effective discount."""
    action: Literal["check_coupon"] = "check_coupon"
    code: str = Field(..., min_length=1, max_length=50)
    order_total: Optional[Decimal] = Field(default=None, description="Provide to show the effective discount amount")


class GetOrderStatusAction(BaseModel):
    """Look up the customer's own orders by order code or get their most recent orders."""
    action: Literal["get_order_status"] = "get_order_status"
    order_code: Optional[str] = Field(default=None, max_length=10)
    limit: int = Field(default=5, ge=1, le=10)


class GetMyAccountAction(BaseModel):
    """Return the customer's bonus balance, referral code, total orders placed, and total amount spent."""
    action: Literal["get_my_account"] = "get_my_account"


class OpenSupportTicketAction(BaseModel):
    """Create a support ticket on behalf of the customer and notify maintainers. Use this to log a written record of an issue."""
    action: Literal["open_support_ticket"] = "open_support_ticket"
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    priority: Literal["low", "normal", "high"] = "normal"
    order_code: Optional[str] = Field(default=None, max_length=10, description="Link to a specific order if relevant")


class StartAppLiveChatAction(BaseModel):
    """Start a live chat session with the platform maintainers (developers). Use for app bugs, payment failures, or technical issues with the bot itself."""
    action: Literal["start_app_live_chat"] = "start_app_live_chat"
    reason: str = Field(..., min_length=5, max_length=500)


class StartStoreLiveChatAction(BaseModel):
    """Start a live chat session with store support staff. Use for order issues, food quality complaints, delivery questions, or refund requests."""
    action: Literal["start_store_live_chat"] = "start_store_live_chat"
    reason: str = Field(..., min_length=5, max_length=500)
    order_code: Optional[str] = Field(default=None, max_length=10, description="Attach to a specific order if relevant")


CUSTOMER_TOOL_SCHEMA_MAP: dict[str, type] = {
    "browse_menu": BrowseMenuAction,
    "get_today_specials": GetTodaySpecialsAction,
    "find_deals": FindDealsAction,
    "find_nearby_stores": FindNearbyStoresAction,
    "check_coupon": CheckCouponAction,
    "get_order_status": GetOrderStatusAction,
    "get_my_account": GetMyAccountAction,
    "open_support_ticket": OpenSupportTicketAction,
    "start_app_live_chat": StartAppLiveChatAction,
    "start_store_live_chat": StartStoreLiveChatAction,
}
