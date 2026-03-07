import json
from datetime import datetime

from fastapi import APIRouter

from db.store import get_db

router = APIRouter()


@router.get("/approvals/pending")
def get_pending():
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return {}

    details = json.loads(row["details_json"])
    return {
        "id": row["id"],
        "shipmentId": row["shipment_id"],
        "action": row["action"],
        **details,
    }


@router.post("/approvals/execute")
def execute_approval(body: dict):
    apr_id = body.get("id")
    with get_db() as conn:
        conn.execute(
            "UPDATE approvals SET status='approved', resolved_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), apr_id),
        )
    return {"success": True}


@router.post("/approvals/reject")
def reject_approval(body: dict):
    apr_id = body.get("id")
    with get_db() as conn:
        conn.execute(
            "UPDATE approvals SET status='rejected', resolved_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), apr_id),
        )
    return {"success": True}
