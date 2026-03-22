"""Tests for Grok tool definition generation (Card 17).

Verifies that Pydantic schemas are correctly converted to OpenAI-compatible
tool definitions with no $ref pointers, correct function names, and
proper parameter schemas.
"""

import json

from bot.ai.schemas import TOOL_SCHEMA_MAP
from bot.ai.tool_defs import ALL_TOOLS, schema_to_tool, _resolve_refs


class TestSchemaToTool:
    def test_tool_count_matches_schema_map(self):
        assert len(ALL_TOOLS) == len(TOOL_SCHEMA_MAP)

    def test_all_tools_have_function_type(self):
        for tool in ALL_TOOLS:
            assert tool["type"] == "function"

    def test_all_tools_have_name_and_description(self):
        for tool in ALL_TOOLS:
            func = tool["function"]
            assert func["name"], "Tool missing name"
            assert func["description"], f"Tool '{func['name']}' missing description"

    def test_tool_names_match_schema_map_keys(self):
        tool_names = {t["function"]["name"] for t in ALL_TOOLS}
        assert tool_names == set(TOOL_SCHEMA_MAP.keys())

    def test_no_action_field_in_parameters(self):
        """The 'action' field should be stripped from tool parameters."""
        for tool in ALL_TOOLS:
            props = tool["function"]["parameters"].get("properties", {})
            assert "action" not in props, (
                f"Tool '{tool['function']['name']}' still has 'action' in parameters"
            )

    def test_no_ref_pointers_in_any_tool(self):
        """$ref must be fully resolved — LLMs don't support JSON Schema references."""
        raw = json.dumps(ALL_TOOLS)
        assert "$ref" not in raw, "Found unresolved $ref in tool definitions"

    def test_required_fields_exclude_action(self):
        for tool in ALL_TOOLS:
            required = tool["function"]["parameters"].get("required", [])
            assert "action" not in required, (
                f"Tool '{tool['function']['name']}' has 'action' in required"
            )


class TestBulkPriceUpdateTool:
    """BulkPriceUpdateAction has a nested model — verify it's inlined."""

    def _get_tool(self):
        for t in ALL_TOOLS:
            if t["function"]["name"] == "bulk_price_update":
                return t
        raise AssertionError("bulk_price_update tool not found")

    def test_updates_is_array(self):
        tool = self._get_tool()
        updates = tool["function"]["parameters"]["properties"]["updates"]
        assert updates["type"] == "array"

    def test_updates_items_have_item_name(self):
        tool = self._get_tool()
        items_schema = tool["function"]["parameters"]["properties"]["updates"]["items"]
        assert "item_name" in items_schema["properties"]

    def test_updates_items_have_new_price(self):
        tool = self._get_tool()
        items_schema = tool["function"]["parameters"]["properties"]["updates"]["items"]
        assert "new_price" in items_schema["properties"]

    def test_updates_min_max_items(self):
        tool = self._get_tool()
        updates = tool["function"]["parameters"]["properties"]["updates"]
        assert updates["minItems"] == 1
        assert updates["maxItems"] == 50


class TestMenuImportTool:
    """MenuImportAction has nested MenuImportRow — verify inlining."""

    def _get_tool(self):
        for t in ALL_TOOLS:
            if t["function"]["name"] == "import_menu":
                return t
        raise AssertionError("import_menu tool not found")

    def test_items_is_array(self):
        tool = self._get_tool()
        items = tool["function"]["parameters"]["properties"]["items"]
        assert items["type"] == "array"

    def test_items_schema_has_item_name(self):
        tool = self._get_tool()
        item_schema = tool["function"]["parameters"]["properties"]["items"]["items"]
        assert "item_name" in item_schema["properties"]

    def test_items_schema_has_price(self):
        tool = self._get_tool()
        item_schema = tool["function"]["parameters"]["properties"]["items"]["items"]
        assert "price" in item_schema["properties"]


class TestResolveRefs:
    def test_resolves_simple_ref(self):
        defs = {"Foo": {"type": "object", "properties": {"x": {"type": "string"}}}}
        obj = {"$ref": "#/$defs/Foo"}
        result = _resolve_refs(obj, defs)
        assert result == defs["Foo"]

    def test_resolves_nested_ref(self):
        defs = {
            "Inner": {"type": "string"},
            "Outer": {"type": "object", "properties": {"val": {"$ref": "#/$defs/Inner"}}},
        }
        obj = {"$ref": "#/$defs/Outer"}
        result = _resolve_refs(obj, defs)
        assert result["properties"]["val"] == {"type": "string"}

    def test_passes_through_non_ref(self):
        result = _resolve_refs({"type": "string"}, {})
        assert result == {"type": "string"}

    def test_handles_lists(self):
        defs = {"X": {"type": "integer"}}
        obj = [{"$ref": "#/$defs/X"}, {"type": "string"}]
        result = _resolve_refs(obj, defs)
        assert result == [{"type": "integer"}, {"type": "string"}]

    def test_handles_scalars(self):
        assert _resolve_refs("hello", {}) == "hello"
        assert _resolve_refs(42, {}) == 42
        assert _resolve_refs(None, {}) is None
