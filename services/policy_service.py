"""A plain REST API, standing in for a team's pre-existing policy system.

No AI, no MCP - just a FastAPI service with its own data, exactly as it might
have existed long before anyone wanted an agent to use it. Run with:

    uvicorn services.policy_service:app --port 8800
"""

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Policy Service (existing system)")

POLICIES = {
    "P-1234": {"status": "active", "premium": 142.50, "renews": "2027-01-01"},
    "P-5678": {"status": "lapsed", "premium": 98.00, "renews": "2026-06-15"},
    "P-9999": {"status": "active", "premium": 210.75, "renews": "2027-03-20"},
}


@app.get("/policies/{policy_id}")
def get_policy(policy_id: str) -> dict:
    policy = POLICIES.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return {"policy_id": policy_id, **policy}
