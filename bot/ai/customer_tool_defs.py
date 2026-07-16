"""OpenAI-compatible tool definitions for the customer Grok assistant (Card 22 + CARD-40 D).

Tools are filtered by capability mask (``ai_customer`` + per-tool caps).
"""

from __future__ import annotations

from typing import Any

from bot.ai.customer_schemas import (
    BrowseMenuAction,
    CheckCouponAction,
    FindDealsAction,
    FindNearbyStoresAction,
    GetMyAccountAction,
    GetOrderStatusAction,
    GetTodaySpecialsAction,
    OpenSupportTicketAction,
    StartAppLiveChatAction,
    StartStoreLiveChatAction,
)
from bot.ai.tool_defs import schema_to_tool
from bot.platform.capabilities import cap_enabled, resolve_capabilities

# Full tool list (unfiltered). Prefer tools_for_channel / tools_for_capabilities.
CUSTOMER_TOOLS = [
    # Catalog (read-only)
    schema_to_tool(BrowseMenuAction),
    schema_to_tool(GetTodaySpecialsAction),
    schema_to_tool(FindDealsAction),
    schema_to_tool(FindNearbyStoresAction),
    schema_to_tool(CheckCouponAction),
    # Own-account (scoped to authenticated user)
    schema_to_tool(GetOrderStatusAction),
    schema_to_tool(GetMyAccountAction),
    # Support
    schema_to_tool(OpenSupportTicketAction),
    schema_to_tool(StartAppLiveChatAction),
    schema_to_tool(StartStoreLiveChatAction),
]

# tool function name → capability key required (in addition to ai_customer)
TOOL_REQUIRED_CAP: dict[str, str] = {
    "browse_menu": "catalog",
    "get_today_specials": "catalog",
    "find_deals": "catalog",
    "find_nearby_stores": "location_once",
    "check_coupon": "checkout",
    "get_order_status": "order_status",
    "get_my_account": "ai_customer",
    "open_support_ticket": "tickets",
    "start_app_live_chat": "tickets",
    "start_store_live_chat": "tickets",
}


def _tool_name(tool: dict[str, Any]) -> str:
    return tool.get("function", {}).get("name") or ""


def tools_for_capabilities(caps: dict[str, bool]) -> list[dict[str, Any]]:
    """Return tools allowed by resolved capability mask (D2)."""
    if not cap_enabled(caps, "ai_customer"):
        return []
    out: list[dict[str, Any]] = []
    for tool in CUSTOMER_TOOLS:
        name = _tool_name(tool)
        required = TOOL_REQUIRED_CAP.get(name, "ai_customer")
        if cap_enabled(caps, required):
            out.append(tool)
    return out


def tools_for_channel(
    channel: str = "telegram",
    *,
    commerce_mode: str | None = "full_store",
    age_gate_enabled: bool = False,
    web_profile: dict[str, Any] | None = None,
    role: str = "customer",
    caps: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """Resolve brand/channel caps (if needed) and filter customer tools."""
    if caps is None:
        caps = resolve_capabilities(
            commerce_mode=commerce_mode,
            age_gate_enabled=age_gate_enabled,
            web_profile=web_profile,
            channel=channel,
            role=role,
        )
    return tools_for_capabilities(caps)


def tool_allowed(func_name: str, caps: dict[str, bool]) -> bool:
    """True if *func_name* may run under *caps*."""
    if not cap_enabled(caps, "ai_customer"):
        return False
    required = TOOL_REQUIRED_CAP.get(func_name)
    if required is None:
        return False
    return cap_enabled(caps, required)
