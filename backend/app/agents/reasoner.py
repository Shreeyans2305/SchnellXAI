from __future__ import annotations

from typing import Dict, List

from .base import AgentContext, AgentOutput, call_gemma_structured
from ..models.domain import AgentEvent, EventType
from ..state import GlobalState


async def run_reasoner(state: GlobalState, observer_output: AgentOutput) -> AgentOutput:
    """
    Reasoner: group observations into hypotheses about root causes and clusters.
    """
    ctx = AgentContext(
        shipments=list(state.shipments.values()),
        locations=list(state.shipment_locations.values()),
        recent_events=list(state.events)[-20:],
    )

    output = AgentOutput()

    # Simple heuristic: identify hubs associated with multiple risky shipments
    risky = next(
        (o for o in observer_output.observations if o["type"] == "risky_shipments"),
        {"items": []},
    )["items"]
    by_carrier: Dict[str, List[dict]] = {}
    for item in risky:
        by_carrier.setdefault(item["carrier"], []).append(item)

    hypotheses: List[dict] = []
    for carrier, shipments in by_carrier.items():
        if len(shipments) >= 2:
            hypotheses.append(
                {
                    "type": "carrier_degradation",
                    "carrier": carrier,
                    "affected_shipments": [s["id"] for s in shipments],
                    "description": f"Multiple at-risk shipments on carrier {carrier}",
                }
            )

    congested = next(
        (o for o in observer_output.observations if o["type"] == "congested_hubs"),
        {"items": []},
    )["items"]
    for hub in congested:
        hypotheses.append(
            {
                "type": "hub_congestion",
                "hub": hub["name"],
                "description": f"Hub {hub['name']} is congested with {hub['shipments']} shipments",
            }
        )

    output.hypotheses = hypotheses

    if hypotheses:
        system = (
            "You are a logistics reasoner. Given hypotheses about delays, "
            "provide a concise narrative (2-3 sentences) explaining likely root causes."
        )
        user = f"Hypotheses: {hypotheses}\nRecent events: {ctx.recent_events[-5:]}\n"
        struct = await call_gemma_structured(system, user)
        if isinstance(struct, dict) and "explanation" in struct:
            output.explanation = str(struct["explanation"])

        ev = AgentEvent(
            id=len(state.events) + 1,
            time="",
            type=EventType.OPTIMIZE,
            flow="reasoner → decider",
            message=f"{len(hypotheses)} hypotheses about emerging risks generated",
        )
        state.enqueue_event(ev)

    return output

