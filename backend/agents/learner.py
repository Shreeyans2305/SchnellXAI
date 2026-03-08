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

SYSTEM_PROMPT = """You are the Learner agent. Evaluate cycle outcomes and extract lessons.
Output ONLY a JSON object with a lessons array."""


def _fallback_lessons(state: AgentState) -> list[dict]:
    lessons = []
    for obs in state.get("observations", [])[:3]:
        lessons.append(
            {
                "pattern_signature_hint": f"{obs.get('type', 'unknown')}::{obs.get('hub', '')}::{obs.get('carrier', '')}",
                "anomaly_type": obs.get("type", "unknown"),
                "hub": obs.get("hub", ""),
                "carrier": obs.get("carrier", ""),
                "description": f"When {obs.get('type', 'anomaly')} appears, pre-emptive reroute reduces delay exposure.",
                "outcome": "SUCCESS" if state.get("executed_actions") else "PARTIAL",
                "recommended_action": "reroute_shipment",
                "confidence_delta": 0.04,
            }
        )
    return lessons


def learner_node(state: AgentState) -> AgentState:
    user_msg = f"""
Observations: {json.dumps(state.get('observations', []))}
Hypotheses: {json.dumps(state.get('hypotheses', []))}
Actions decided: {json.dumps(state.get('actions', []))}
Executed actions: {json.dumps(state.get('executed_actions', []))}

Extract lessons and patterns to remember.
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
            result = {"lessons": _fallback_lessons(state)}
    except Exception:
        result = {"lessons": _fallback_lessons(state)}

    lessons = result.get("lessons", [])
    # Guard: LLM may return lessons as strings instead of dicts
    lessons = [l for l in lessons if isinstance(l, dict)]
    now = datetime.utcnow().isoformat()
    cycle_id = state.get("cycle_id", "?")

    for lesson in lessons:
        long_term_memory.upsert_pattern(
            anomaly_type=lesson.get("anomaly_type", "unknown"),
            hub=lesson.get("hub", ""),
            carrier=lesson.get("carrier", ""),
            description=lesson.get("description", ""),
            outcome=lesson.get("outcome", "SUCCESS"),
            recommended_action=lesson.get("recommended_action", ""),
        )
        short_term_memory.push(
            ShortTermEvent(
                cycle_id=cycle_id,
                timestamp=now,
                event_type="LEARNING",
                flow="learner → all",
                message=lesson.get("description", "Pattern learned"),
                metadata=lesson,
            )
        )

    return {
        **state,
        "lessons": lessons,
        "learner_summary": f"Learned {len(lessons)} patterns, updated long-term memory.",
    }
