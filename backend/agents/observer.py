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


def _fallback_observations(shipments: list[dict], hubs: list[dict] | None = None) -> list[dict]:
    out = []

    # Build set of congested hub names for accurate flagging
    congested_hubs: set[str] = set()
    for h in (hubs or []):
        if h.get("status") == "congested":
            name = h.get("name", "").replace(" Hub", "").strip()
            if name:
                congested_hubs.add(name.lower())

    for s in shipments:
        risk = int(s.get("risk", 0))
        if risk < settings.risk_anomaly_threshold:
            continue

        route_str = str(s.get("route", "Unknown → Unknown"))
        route_parts = [p.strip() for p in route_str.split("→")] if "→" in route_str else ["Unknown"]

        # Determine the actual problematic hub — prefer congested hub on route
        hub = "Unknown"
        for part in route_parts:
            if part.lower() in congested_hubs:
                hub = part
                break
        if hub == "Unknown":
            # No congested hub on this route — use origin as fallback
            hub = route_parts[0] if route_parts else "Unknown"

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

    # Collect pre-buffered anomalies from the scheduler
    buffered = state.get("buffered_anomalies", [])
    history = state.get("anomaly_history", [])

    # Summarise buffered disruptions so the LLM knows what happened
    buffered_summary = "No disruptions reported in this window."
    if buffered:
        lines = []
        for b in buffered:
            lines.append(
                f"- [{b.get('type','?')}] severity={b.get('severity',0)} "
                f"shipment={b.get('targetShipmentId','?')} hub={b.get('targetWarehouseId','?')} "
                f"at {b.get('buffered_at','?')}"
            )
        buffered_summary = f"{len(buffered)} disruptions buffered:\n" + "\n".join(lines)

    # Summarise recent anomaly history (long-term, for learning context only)
    history_summary = "No prior anomaly history."
    if history:
        history_lines = []
        for h in history[:15]:
            history_lines.append(
                f"- [{h.get('type','?')}] sev={h.get('severity',0)} "
                f"ship={h.get('target_shipment','')} hub={h.get('target_hub','')} "
                f"at {h.get('timestamp','?')}"
            )
        history_summary = f"Recent anomaly history ({len(history)} total, showing last {len(history_lines)}):\n" + "\n".join(history_lines)

    user_msg = f"""
Recent event history (short-term memory):
{recent_ctx}

--- BUFFERED DISRUPTIONS (this cycle) ---
{buffered_summary}

--- ANOMALY HISTORY (long-term, for learning — do NOT act on these directly) ---
{history_summary}

Current shipments:
{json.dumps(state['shipments'], indent=2)}

Current hubs:
{json.dumps(state['hubs'], indent=2)}

Carriers:
{json.dumps(state['carriers'], indent=2)}

Detect all anomalies in the CURRENT data. Consider the buffered disruptions above.
Use anomaly history only as context to recognise patterns — do NOT re-flag old events.
Return JSON array only.
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
            observations = _fallback_observations(state.get("shipments", []), state.get("hubs", []))
    except Exception:
        observations = _fallback_observations(state.get("shipments", []), state.get("hubs", []))

    # ── Severity gate: drop observations below the risk threshold ──
    observations = [
        o for o in observations
        if int(o.get("severity", 0)) >= settings.risk_anomaly_threshold
    ]

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

    summary = (
        f"Observer flagged {len(observations)} anomalies "
        f"(from {len(buffered)} buffered disruptions, {len(history)} history entries)."
    )
    return {**state, "observations": observations, "observer_summary": summary, "cycle_id": cycle_id}
