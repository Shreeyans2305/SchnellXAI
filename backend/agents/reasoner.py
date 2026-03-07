import json
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from agents.state import AgentState
from config import settings
from memory.long_term import long_term_memory
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory

llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)

SYSTEM_PROMPT = """You are the Reasoner agent in a logistics AI system.
Given a list of anomalies and historical context, produce hypotheses about root causes and patterns.
Output ONLY a JSON object:
{
  "hypotheses": [{ "type": str, "confidence": 0-1, "affected_shipments": [str], "hub": str,
                   "carrier": str, "root_cause": str, "cascade_risk": str }],
  "patterns_detected": [str],
  "recommendation_hints": [str]
}
No explanation outside the JSON."""


def _fallback_reasoning(observations: list[dict]) -> dict:
    hypotheses = []
    patterns = []
    for obs in observations:
        risk = int(obs.get("severity", 60))
        hypothesis_type = "hub_congestion" if obs.get("type") in {"hub_congestion", "late_pickup"} else "carrier_degradation"
        hypotheses.append(
            {
                "type": hypothesis_type,
                "confidence": round(min(0.95, 0.45 + risk / 200), 2),
                "affected_shipments": [obs.get("shipment_id", "?")],
                "hub": obs.get("hub", "Unknown"),
                "carrier": obs.get("carrier", "Unknown"),
                "root_cause": f"Likely driven by {obs.get('type', 'operational anomaly')} at {obs.get('hub', 'hub')}",
                "cascade_risk": "medium" if risk < 80 else "high",
            }
        )
        patterns.append(f"{obs.get('type', 'anomaly')}::{obs.get('hub', 'hub')}::{obs.get('carrier', 'carrier')}")
    return {"hypotheses": hypotheses, "patterns_detected": patterns, "recommendation_hints": []}


def reasoner_node(state: AgentState) -> AgentState:
    observations = state.get("observations", [])
    if not observations:
        return {
            **state,
            "hypotheses": [],
            "patterns_detected": [],
            "reasoner_summary": "No anomalies to reason about.",
        }

    pattern_context_parts = []
    for obs in observations:
        p = long_term_memory.lookup_pattern(obs.get("type", ""), obs.get("hub", ""), obs.get("carrier", ""))
        if p:
            pattern_context_parts.append(
                f"- {p.description}: seen {p.occurrences}x, confidence {p.avg_confidence:.0%}, recommended: {p.recommended_action}"
            )

    pattern_context = "\n".join(pattern_context_parts) if pattern_context_parts else "No matching historical patterns."

    user_msg = f"""
Anomalies detected by Observer:
{json.dumps(observations, indent=2)}

Matching historical patterns from long-term memory:
{pattern_context}

Recent short-term context:
{short_term_memory.to_context_string(8)}

Reason about root causes and output JSON.
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
            result = _fallback_reasoning(observations)
    except Exception:
        result = _fallback_reasoning(observations)

    hypotheses = result.get("hypotheses", [])
    patterns = result.get("patterns_detected", [])

    cycle_id = state.get("cycle_id", "?")
    for h in hypotheses:
        short_term_memory.push(
            ShortTermEvent(
                cycle_id=cycle_id,
                timestamp=datetime.utcnow().isoformat(),
                event_type="OPTIMIZE",
                flow="reasoner → decider",
                message=f"{h.get('type', '?')}: {h.get('root_cause', '')}",
                metadata=h,
            )
        )

    return {
        **state,
        "hypotheses": hypotheses,
        "patterns_detected": patterns,
        "reasoner_summary": f"Identified {len(hypotheses)} hypotheses, {len(patterns)} patterns.",
    }
