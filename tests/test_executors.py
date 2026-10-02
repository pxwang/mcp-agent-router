from mcp_agent_router.executors import get_policy_status, schedule_appointment, search_faq


def test_get_policy_status_known_policy():
    result = get_policy_status("P-1234")
    assert result == {
        "policy_id": "P-1234",
        "status": "active",
        "premium": 142.50,
        "renews": "2027-01-01",
    }


def test_get_policy_status_unknown_policy():
    result = get_policy_status("P-0000")
    assert result == {"error": "Policy P-0000 not found"}


def test_schedule_appointment_defaults_topic():
    result = schedule_appointment(date="2026-10-05", time="14:00")
    assert result == {
        "confirmed": True,
        "date": "2026-10-05",
        "time": "14:00",
        "topic": "general",
    }


def test_search_faq_matches_keywords():
    result = search_faq("What is a deductible?")
    assert result["matches"]
    assert "deductible" in result["matches"][0]["answer"].lower()


def test_search_faq_no_match():
    result = search_faq("xyzzy unrelated gibberish")
    assert result["matches"] == []
