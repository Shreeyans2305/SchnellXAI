import json
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from agents.state import AgentState
from config import settings
from db.store import get_db
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory

llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)

SYSTEM_PROMPT = f"""You are the Decider agent in a logistics AI system.
Given hypotheses and constraints, decide which actions to take.
Autonomy rules:
  - autonomous=true when risk < {settings.human_approval_threshold} AND cost_delta_inr < {settings.auto_act_threshold * 100}
  - autonomous=false when risk >= {settings.human_approval_threshold} OR cost is high

Output ONLY a JSON object with actions and queued_approvals."""


def _fallback_actions(hypotheses: list[dict]) -> dict:
    actions = []
    approvals = []
    for h in hypotheses:
        sid = (h.get("affected_shipments") or ["?"])[0]
        risk = int(100 * float(h.get("confidence", 0.6)))
        cost = 1500 + risk * 25
        act = {
            "id": f"ACT-{str(uuid.uuid4())[:8].upper()}",
            "type": "reroute_shipment",
            "target_shipment_id": sid,
            "params": {
                "shipment_id": sid,
                "new_route": [h.get("hub", "Mumbai"), "Pune", "Delhi"],
                "carrier": h.get("carrier", "BlueDart"),
                "eta_delta_minutes": 90,
            },
            "autonomous": risk < settings.human_approval_threshold and cost < settings.auto_act_threshold * 100,
            "risk_score": risk,
            "cost_delta_inr": cost,
            "rationale": h.get("root_cause", "Fallback decision based on risk."),
        }
        actions.append(act)
        if not act["autonomous"]:
            approvals.append(
                {
                    "id": f"APR-{str(uuid.uuid4())[:8].upper()}",
                    "shipment_id": sid,
                    "action": f"Reroute {sid}",
                    "reason": act["rationale"],
                    "cost_delta": f"+₹{cost:,}",
                    "sla_impact": "+2h",
                    "current_route": ["Mumbai", "Nagpur", "Delhi"],
                    "proposed_route": act["params"]["new_route"],
                    "net_score": max(10, 100 - act["risk_score"]),
                    "blast_radius": 2,
                }
            )
    return {"actions": actions, "queued_approvals": approvals}


def decider_node(state: AgentState) -> AgentState:
    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        return {**state, "actions": [], "queued_approvals": [], "decider_summary": "No action needed."}

    user_msg = f"""
Hypotheses from Reasoner:
{json.dumps(hypotheses, indent=2)}

Current shipments:
{json.dumps(state['shipments'], indent=2)}

Decide on actions. Output JSON only.
"""

    try:
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```", maxsplit=2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        if not isinstance(result, dict):
            result = _fallback_actions(hypotheses)
    except Exception:
        result = _fallback_actions(hypotheses)

    actions = result.get("actions", [])
    approvals = result.get("queued_approvals", [])

    now = datetime.utcnow().isoformat()
    cycle_id = state.get("cycle_id", "?")
    with get_db() as conn:
        for apr in approvals:
            apr.setdefault("id", f"APR-{str(uuid.uuid4())[:8].upper()}")
            conn.execute(
                """
                INSERT OR REPLACE INTO approvals
                (id, shipment_id, action, details_json, status, created_at)
                VALUES (?,?,?,?,?,?)
            """,
                (
                    apr["id"],
                    apr.get("shipment_id", "?"),
                    apr.get("action", "?"),
                    json.dumps(apr),
                    "pending",
                    now,
                ),
            )
            short_term_memory.push(
                ShortTermEvent(
                    cycle_id=cycle_id,
                    timestamp=now,
                    event_type="APPROVAL",
                    flow="decider → human",
                    message=f"{apr.get('shipment_id', '?')} requires approval — {apr.get('action', '')}",
                    metadata=apr,
                )
            )

    for act in actions:
        if act.get("autonomous"):
            short_term_memory.push(
                ShortTermEvent(
                    cycle_id=cycle_id,
                    timestamp=now,
                    event_type="REROUTE" if act.get("type") == "reroute_shipment" else "EXECUTE",
                    flow="decider → executor",
                    message=f"{act.get('target_shipment_id', '?')} — {act.get('rationale', '')}",
                    metadata=act,
                )
            )

    return {
        **state,
        "actions": actions,
        "queued_approvals": approvals,
        "decider_summary": f"{len(actions)} actions decided, {len(approvals)} pending approval.",
    }
