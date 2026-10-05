import mcp_agent_router.tools as tools_module
from mcp_agent_router.tools import ToolRegistry


def test_anthropic_tools_lists_all_enabled_tools():
    registry = ToolRegistry()
    names = {t["name"] for t in registry.anthropic_tools()}
    assert names == {"get_policy_status", "schedule_appointment", "search_faq"}


def test_every_tool_has_a_description_and_schema():
    registry = ToolRegistry()
    for tool in registry.anthropic_tools():
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"


def test_call_dispatches_to_executor():
    registry = ToolRegistry()
    result = registry.call("get_policy_status", {"policy_id": "P-1234"})
    assert result["status"] == "active"


def test_call_unknown_tool_is_rejected():
    registry = ToolRegistry()
    result = registry.call("delete_everything", {})
    assert "error" in result


def test_get_policy_status_routes_to_mcp_when_backend_is_mcp(monkeypatch):
    monkeypatch.setattr(tools_module, "_POLICY_BACKEND", "mcp")
    monkeypatch.setattr(
        tools_module, "call_policy_mcp_tool", lambda policy_id: {"policy_id": policy_id, "via": "mcp"}
    )
    registry = ToolRegistry()
    result = registry.call("get_policy_status", {"policy_id": "P-1234"})
    assert result == {"policy_id": "P-1234", "via": "mcp"}


def test_other_tools_are_unaffected_by_policy_backend(monkeypatch):
    monkeypatch.setattr(tools_module, "_POLICY_BACKEND", "mcp")
    registry = ToolRegistry()
    result = registry.call("search_faq", {"query": "deductible"})
    assert result["matches"]
