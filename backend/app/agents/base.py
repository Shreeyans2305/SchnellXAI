from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..llm import get_ollama_client
from ..models.domain import (
    AgentAction,
    AgentEvent,
    CascadeImpact,
    Shipment,
    ShipmentLocation,
)
from ..state import GlobalState


@dataclass
class AgentContext:
    """Lightweight view over global state passed into each agent."""

    shipments: List[Shipment]
    locations: List[ShipmentLocation]
    recent_events: List[AgentEvent]


@dataclass
class AgentOutput:
    """Structured agent output shared across pipeline stages."""

    observations: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    cascade_impacts: List[CascadeImpact] = field(default_factory=list)
    explanation: str = ""


async def call_gemma_structured(
    system_prompt: str, user_prompt: str
) -> Dict[str, Any]:
    """
    Helper to call Gemma via Ollama and parse structured JSON where possible.

    Falls back to an empty dict on errors, letting the caller rely on
    deterministic heuristics.
    """
    client = get_ollama_client()
    messages = [{"role": "user", "content": user_prompt}]
    return await client.chat_json(system_prompt, messages)


def build_agent_context(state: GlobalState) -> AgentContext:
    return AgentContext(
        shipments=list(state.shipments.values()),
        locations=list(state.shipment_locations.values()),
        recent_events=list(state.events)[-20:],
    )

