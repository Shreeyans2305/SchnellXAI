import json
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from agents.state import AgentState
from config import settings
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory

llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)

SYSTEM_PROMPT = """You are the Observer agent in a logistics AI system.
Your job: scan the incoming shipment and hub data, detect anomalies, and output ONLY a JSON array.
Each element must have: { type, shipment_id, hub, carrier, severity (0-100), description }
Anomaly types to detect: late_pickup | hub_congestion | carrier_degradation | eta_mismatch |
                          temperature_excursion | sla_breach_risk | inventory_mismatch
Return [] if no anomalies are found. Output ONLY valid JSON, no explanation."""


def _fallback_observations(shipments: list[dict]) -> list[dict]:
    out = []
    for s in shipments:
        risk = int(s.get("risk", 0))
        if risk >= settings.risk_anomaly_threshold:
            route = str(s.get("route", "Unknown → Unknown")).split(" → ")
            hub = route[0] if route else "Unknown"
            out.append(
                {
                    "type": "sla_breach_risk" if risk < 85 else "late_pickup",
                    "shipment_id": s.get("id", "?"),
                    "hub": hub,
                    "carrier": s.get("carrier", "Unknown"),
                    "severity": risk,
                    "description": f"Risk score {risk} exceeds threshold {settings.risk_anomaly_threshold}",
                }
            )
    return out


def observer_node(state: AgentState) -> AgentState:
    recent_ctx = short_term_memory.to_context_string(10)

    user_msg = f"""
Recent event history (short-term memory):
{recent_ctx}

Current shipments:
{json.dumps(state['shipments'], indent=2)}

Current hubs:
{json.dumps(state['hubs'], indent=2)}

Carriers:
{json.dumps(state['carriers'], indent=2)}

Detect all anomalies. Return JSON array only.
"""

    observations: list[dict]
    try:
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```", maxsplit=2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        observations = json.loads(raw.strip())
        if not isinstance(observations, list):
            observations = _fallback_observations(state.get("shipments", []))
    except Exception:
        observations = _fallback_observations(state.get("shipments", []))

    cycle_id = state.get("cycle_id", str(uuid.uuid4())[:8])
    for obs in observations:
        short_term_memory.push(
            ShortTermEvent(
                cycle_id=cycle_id,
                timestamp=datetime.utcnow().isoformat(),
                event_type="ANOMALY",
                flow="observer → reasoner",
                message=f"{obs.get('shipment_id', '?')} {obs.get('description', '')}",
                metadata=obs,
            )
        )

    summary = f"Observer flagged {len(observations)} anomalies."
    return {**state, "observations": observations, "observer_summary": summary, "cycle_id": cycle_id}
