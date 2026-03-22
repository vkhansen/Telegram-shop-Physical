"""Convert Pydantic schemas to OpenAI-compatible tool definitions (Card 17)."""

from bot.ai.schemas import (
    AdjustStockAction,
    BulkPriceUpdateAction,
    CreateCategoryAction,
    CreateItemAction,
    DataMappingProposal,
    DeleteCategoryAction,
    DeleteItemAction,
    GetStatsAction,
    LookupUserAction,
    MenuImportAction,
    SearchChatMessagesAction,
    SearchDeliveriesAction,
    SearchOrdersAction,
    UpdateItemAction,
    ViewInventoryAction,
)


def _resolve_refs(obj, defs: dict):
    """Recursively resolve $ref pointers using the $defs dict.

    Many LLM function-calling endpoints (including xAI/Grok) do not support
    JSON Schema ``$ref``.  This helper inlines every reference so the schema
    is fully self-contained.
    """
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref_path = obj["$ref"]  # e.g. "#/$defs/BulkPriceUpdateEntry"
            ref_name = ref_path.rsplit("/", 1)[-1]
            resolved = defs.get(ref_name, obj)
            # Recurse into the resolved definition (it may contain refs too)
            return _resolve_refs(resolved, defs)
        return {k: _resolve_refs(v, defs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_refs(item, defs) for item in obj]
    return obj


def schema_to_tool(model_class) -> dict:
    """Convert a Pydantic model to an OpenAI-format tool definition.

    Uses the action field's default value as the function name so it matches
    the keys in TOOL_SCHEMA_MAP (e.g. 'create_item', not 'CreateItemAction').
    Inlines all ``$ref`` pointers for LLM compatibility.
    """
    schema = model_class.model_json_schema()
    defs = schema.pop("$defs", {})

    props = dict(schema.get("properties", {}))
    props.pop("action", None)
    required = [r for r in schema.get("required", []) if r != "action"]

    # Resolve any $ref pointers in properties
    props = _resolve_refs(props, defs)

    # Extract the action literal value for the function name
    action_schema = schema.get("properties", {}).get("action", {})
    func_name = action_schema.get("const") or action_schema.get("default") or schema.get("title", model_class.__name__)

    return {
        "type": "function",
        "function": {
            "name": func_name,
            "description": model_class.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        },
    }


ALL_TOOLS = [
    schema_to_tool(CreateItemAction),
    schema_to_tool(UpdateItemAction),
    schema_to_tool(DeleteItemAction),
    schema_to_tool(BulkPriceUpdateAction),
    schema_to_tool(AdjustStockAction),
    schema_to_tool(CreateCategoryAction),
    schema_to_tool(DeleteCategoryAction),
    schema_to_tool(SearchOrdersAction),
    schema_to_tool(SearchChatMessagesAction),
    schema_to_tool(SearchDeliveriesAction),
    schema_to_tool(LookupUserAction),
    schema_to_tool(GetStatsAction),
    schema_to_tool(ViewInventoryAction),
    schema_to_tool(MenuImportAction),
    schema_to_tool(DataMappingProposal),
]
