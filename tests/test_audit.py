from mcp_agent_router.audit import log_tool_call, recent_tool_calls


def test_log_tool_call_records_success():
    log_tool_call(
        query="What's the status of policy P-1234?",
        tool_name="get_policy_status",
        arguments={"policy_id": "P-1234"},
        latency_ms=12.5,
        success=True,
    )
    logs = recent_tool_calls()
    assert len(logs) == 1
    assert logs[0]["tool_name"] == "get_policy_status"
    assert logs[0]["success"] == 1
    assert logs[0]["error"] is None


def test_log_tool_call_records_failure():
    log_tool_call(
        query="What's the status of policy P-0000?",
        tool_name="get_policy_status",
        arguments={"policy_id": "P-0000"},
        latency_ms=5.0,
        success=False,
        error="Policy P-0000 not found",
    )
    logs = recent_tool_calls()
    assert logs[0]["success"] == 0
    assert logs[0]["error"] == "Policy P-0000 not found"


def test_recent_tool_calls_orders_newest_first():
    log_tool_call("q1", "search_faq", {"query": "q1"}, 1.0, True)
    log_tool_call("q2", "search_faq", {"query": "q2"}, 1.0, True)
    logs = recent_tool_calls()
    assert logs[0]["query"] == "q2"
    assert logs[1]["query"] == "q1"
