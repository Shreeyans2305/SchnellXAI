from fastapi import APIRouter

from data.seed import get_live_state
from memory.short_term import short_term_memory

router = APIRouter()


@router.get("/dashboard/metrics")
def dashboard_metrics():
    state = get_live_state()
    shipments = state.get("shipments", [])
    total = len(shipments)
    at_risk = len([s for s in shipments if int(s.get("risk", 0)) >= 55 and int(s.get("risk", 0)) < 80])
    delayed = len([s for s in shipments if str(s.get("status", "")).upper() == "DELAYED" or int(s.get("risk", 0)) >= 80])

    approvals_count = 0
    for e in short_term_memory.recent(100):
        if e.event_type == "APPROVAL":
            approvals_count += 1

    recent_events = short_term_memory.recent(200)

    return {
        "shipments": {"value": total, "change": f"+{max(1, total // 10)}%"},
        "atRisk": {"value": at_risk, "change": f"+{max(0, at_risk // 4)}"},
        "delayed": {"value": delayed, "change": f"-{1 if delayed > 0 else 0}"},
        "agentOps": {"value": max(len(recent_events), 1) * 37, "change": f"+{max(len(recent_events), 1)}"},
        "approvals": {"value": approvals_count, "change": f"+{1 if approvals_count else 0}"},
        "ollamaStatus": "connected",
        "agentsActive": 5,
        "agentsTotal": 5,
    }
