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

CRITICAL: Only escalate hypotheses that show a REAL pattern.  Mark each hypothesis with:
  pattern_strength: "strong" | "moderate" | "weak"

A pattern is STRONG when:
  - Multiple congestion events at the SAME hub/warehouse
  - Multiple late shipments or delays from the SAME carrier (e.g. BlueDart, Delhivery)
  - Cascading reroutes (one reroute causing downstream delays)
  - Repeated ETA mismatches on the same route or corridor
  - 3+ anomalies of any type that are correlated

A pattern is MODERATE when:
  - 2 related anomalies (same hub OR same carrier OR same type)
  - One anomaly that matches a known historical pattern from long-term memory

A pattern is WEAK when:
  - A single isolated anomaly with no corroboration
  - Low severity (<60) one-off events

Output ONLY a JSON object:
{
  "hypotheses": [{ "type": str, "confidence": 0-1, "affected_shipments": [str], "hub": str,
                   "carrier": str, "root_cause": str, "cascade_risk": str,
                   "pattern_strength": "strong"|"moderate"|"weak",
                   "evidence_count": int }],
  "patterns_detected": [str],
  "recommendation_hints": [str]
}
No explanation outside the JSON."""


def _fallback_reasoning(observations: list[dict], history: list[dict] | None = None) -> dict:
    """Group observations to detect real patterns; suppress isolated noise."""
    history = history or []

    # --- Pre-filter: drop low-severity observations entirely ---
    observations = [o for o in observations if int(o.get("severity", 0)) >= 60]
    if not observations:
        return {"hypotheses": [], "patterns_detected": [], "recommendation_hints": []}

    # --- Grouping: by hub, carrier, and anomaly type ---
    by_hub: dict[str, list[dict]] = {}
    by_carrier: dict[str, list[dict]] = {}
    by_type: dict[str, list[dict]] = {}
    for obs in observations:
        hub = obs.get("hub", "Unknown").strip()
        carrier = obs.get("carrier", "Unknown").strip()
        atype = obs.get("type", "unknown")
        if hub and hub != "Unknown":
            by_hub.setdefault(hub, []).append(obs)
        if carrier and carrier != "Unknown":
            by_carrier.setdefault(carrier, []).append(obs)
        by_type.setdefault(atype, []).append(obs)

    # Count matching history entries for each key
    def _history_count(key_type: str, key_val: str) -> int:
        key_lower = key_val.lower()
        count = 0
        for h in history:
            if key_type == "hub" and key_lower in h.get("target_hub", "").lower():
                count += 1
            elif key_type == "carrier" and key_lower in h.get("payload_json", "").lower():
                count += 1
            elif key_type == "type" and h.get("type", "").lower() == key_lower:
                count += 1
        return count

    hypotheses = []
    patterns = []

    # --- Hub-level patterns (congestion) ---
    for hub, obs_list in by_hub.items():
        total_evidence = len(obs_list) + _history_count("hub", hub)
        if total_evidence < 2:
            continue  # isolated single event at this hub
        avg_sev = sum(int(o.get("severity", 60)) for o in obs_list) / len(obs_list)
        strength = "strong" if total_evidence >= 3 else "moderate"
        hypotheses.append({
            "type": "hub_congestion",
            "confidence": round(min(0.95, 0.5 + total_evidence * 0.1), 2),
            "affected_shipments": [o.get("shipment_id", "?") for o in obs_list],
            "hub": hub,
            "carrier": obs_list[0].get("carrier", "Unknown"),
            "root_cause": f"Recurring congestion at {hub} ({total_evidence} correlated events)",
            "cascade_risk": "high" if avg_sev >= 75 else "medium",
            "pattern_strength": strength,
            "evidence_count": total_evidence,
        })
        patterns.append(f"hub_congestion::{hub}")

    # --- Carrier-level patterns (degradation) ---
    for carrier, obs_list in by_carrier.items():
        total_evidence = len(obs_list) + _history_count("carrier", carrier)
        if total_evidence < 2:
            continue
        avg_sev = sum(int(o.get("severity", 60)) for o in obs_list) / len(obs_list)
        strength = "strong" if total_evidence >= 3 else "moderate"
        # Avoid duplicating if already covered by hub hypothesis
        covered_sids = {s for h in hypotheses for s in h.get("affected_shipments", [])}
        new_sids = [o.get("shipment_id", "?") for o in obs_list if o.get("shipment_id") not in covered_sids]
        if not new_sids:
            continue
        hypotheses.append({
            "type": "carrier_degradation",
            "confidence": round(min(0.95, 0.45 + total_evidence * 0.1), 2),
            "affected_shipments": new_sids,
            "hub": obs_list[0].get("hub", "Unknown"),
            "carrier": carrier,
            "root_cause": f"Repeated issues with {carrier} ({total_evidence} incidents)",
            "cascade_risk": "high" if avg_sev >= 75 else "medium",
            "pattern_strength": strength,
            "evidence_count": total_evidence,
        })
        patterns.append(f"carrier_degradation::{carrier}")

    # --- Type-level patterns (e.g. recurring eta_mismatch, cascading reroutes) ---
    for atype, obs_list in by_type.items():
        if atype in ("hub_congestion", "late_pickup"):  # already handled above
            continue
        total_evidence = len(obs_list) + _history_count("type", atype)
        if total_evidence < 2:
            continue
        covered_sids = {s for h in hypotheses for s in h.get("affected_shipments", [])}
        new_sids = [o.get("shipment_id", "?") for o in obs_list if o.get("shipment_id") not in covered_sids]
        if not new_sids:
            continue
        strength = "strong" if total_evidence >= 3 else "moderate"
        hypotheses.append({
            "type": atype,
            "confidence": round(min(0.90, 0.4 + total_evidence * 0.1), 2),
            "affected_shipments": new_sids,
            "hub": obs_list[0].get("hub", "Unknown"),
            "carrier": obs_list[0].get("carrier", "Unknown"),
            "root_cause": f"Pattern of {atype.replace('_', ' ')} events ({total_evidence} occurrences)",
            "cascade_risk": "medium",
            "pattern_strength": strength,
            "evidence_count": total_evidence,
        })
        patterns.append(f"{atype}::recurring")

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

    # Include anomaly history for learning context
    history = state.get("anomaly_history", [])
    history_context = "No prior anomaly history."
    if history:
        h_lines = []
        for h in history[:10]:
            h_lines.append(
                f"- [{h.get('type','?')}] sev={h.get('severity',0)} "
                f"ship={h.get('target_shipment','')} hub={h.get('target_hub','')} "
                f"at {h.get('timestamp','?')}"
            )
        history_context = f"Recent anomaly log ({len(history)} entries, showing last {len(h_lines)}):\\n" + "\\n".join(h_lines)

    user_msg = f"""
Anomalies detected by Observer:
{json.dumps(observations, indent=2)}

Matching historical patterns from long-term memory:
{pattern_context}

Anomaly history log (for learning — do NOT re-raise past events):
{history_context}

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
            result = _fallback_reasoning(observations, state.get("anomaly_history", []))
    except Exception:
        result = _fallback_reasoning(observations, state.get("anomaly_history", []))

    raw_hypotheses = result.get("hypotheses", [])
    raw_hypotheses = [h for h in raw_hypotheses if isinstance(h, dict)]  # guard
    patterns = result.get("patterns_detected", [])

    # ── Pattern-strength gate: only escalate moderate/strong hypotheses ──
    hypotheses = []
    suppressed = []
    for h in raw_hypotheses:
        strength = h.get("pattern_strength", "weak").lower()
        evidence = int(h.get("evidence_count", 1))
        if strength in ("strong", "moderate") or evidence >= 2:
            hypotheses.append(h)
        else:
            suppressed.append(h)

    cycle_id = state.get("cycle_id", "?")

    # Log suppressed weak signals as MONITOR events (visible in activity stream)
    for h in suppressed:
        short_term_memory.push(
            ShortTermEvent(
                cycle_id=cycle_id,
                timestamp=datetime.utcnow().isoformat(),
                event_type="MONITOR",
                flow="reasoner → observer",
                message=(
                    f"Monitoring: {h.get('type', '?')} at {h.get('hub', '?')} "
                    f"({h.get('carrier', '?')}) — isolated event, no action needed yet"
                ),
                metadata=h,
            )
        )

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
        "reasoner_summary": (
            f"Identified {len(hypotheses)} actionable patterns, "
            f"{len(suppressed)} weak signals suppressed (monitoring)."
        ),
    }
