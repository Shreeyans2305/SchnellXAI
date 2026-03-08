from fastapi import APIRouter

from data.seed import get_live_state
from db.store import get_db
from memory.short_term import short_term_memory

router = APIRouter()


@router.get("/dashboard/metrics")
def dashboard_metrics():
    state = get_live_state()
    shipments = state.get("shipments", [])

    # ── Shipments ──
    total = len(shipments)

    # ── At Risk: risk between 55-79 AND not already DELAYED ──
    at_risk = len([
        s for s in shipments
        if 55 <= int(s.get("risk", 0)) < 80
        and str(s.get("status", "")).upper() != "DELAYED"
    ])

    # ── Delayed: status is DELAYED or risk >= 80 ──
    delayed = len([
        s for s in shipments
        if str(s.get("status", "")).upper() == "DELAYED"
        or int(s.get("risk", 0)) >= 80
    ])

    # ── Agent Ops: real count from short-term event buffer + DB action_log ──
    stm_count = len(short_term_memory.recent(1000))
    try:
        with get_db() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM action_log").fetchone()
            db_ops = row["cnt"] if row else 0
    except Exception:
        db_ops = 0
    agent_ops = stm_count + db_ops

    # ── Approvals: real count of pending approvals from DB ──
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM approvals WHERE status='pending'"
            ).fetchone()
            pending_approvals = row["cnt"] if row else 0
    except Exception:
        pending_approvals = 0

    return {
        "shipments": {"value": total, "change": f"{total} active"},
        "atRisk": {"value": at_risk, "change": f"of {total}" if total else "—"},
        "delayed": {"value": delayed, "change": f"of {total}" if total else "—"},
        "agentOps": {"value": agent_ops, "change": f"{stm_count} recent"},
        "approvals": {"value": pending_approvals, "change": "pending"},
        "ollamaStatus": "connected",
        "agentsActive": 5,
        "agentsTotal": 5,
    }
