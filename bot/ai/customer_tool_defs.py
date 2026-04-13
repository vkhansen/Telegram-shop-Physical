"""OpenAI-compatible tool definitions for the customer Grok assistant (Card 22).

Re-uses the schema_to_tool() helper from the admin tool_defs module.
"""

from bot.ai.tool_defs import schema_to_tool
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
