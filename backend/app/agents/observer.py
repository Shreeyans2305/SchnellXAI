from __future__ import annotations

from typing import List

from .base import AgentContext, AgentOutput, call_gemma_structured
from ..models.domain import AgentEvent, EventType, ShipmentStatus
from ..state import GlobalState


async def run_observer(state: GlobalState) -> AgentOutput:
    """
    Observer: scan raw signals and detect anomalies / at-risk elements.
    """
    ctx = AgentContext(
        shipments=list(state.shipments.values()),
        locations=list(state.shipment_locations.values()),
        recent_events=list(state.events)[-20:],
    )

    output = AgentOutput()

    # Heuristic detection of anomalies and risks
    risky_shipments: List[dict] = []
    for s in ctx.shipments:
        if s.risk >= 70 or s.status in (ShipmentStatus.AT_RISK, ShipmentStatus.DELAYED):
            risky_shipments.append(
                {
                    "id": s.id,
                    "route": s.route,
                    "carrier": s.carrier,
                    "risk": s.risk,
                    "status": s.status.value,
                    "notes": s.notes,
                }
            )

    congested_hubs = [
        {
            "id": h.id,
            "name": h.name,
            "shipments": h.shipments,
            "status": h.status,
        }
        for h in state.hubs.values()
        if h.status != "active"
    ]

    output.observations = [
        {"type": "risky_shipments", "items": risky_shipments},
        {"type": "congested_hubs", "items": congested_hubs},
    ]

    # Optional Gemma summary
    if risky_shipments or congested_hubs:
        system = (
            "You are an operations observer for an Indian logistics network. "
            "Summarize key risk observations in 2-3 short sentences."
        )
        user = (
            "Risky shipments:\n"
            f"{risky_shipments}\n\n"
            "Congested hubs:\n"
            f"{congested_hubs}\n"
        )
        struct = await call_gemma_structured(system, user)
        if isinstance(struct, dict) and "summary" in struct:
            output.explanation = str(struct["summary"])

    if risky_shipments:
        ev = AgentEvent(
            id=len(state.events) + 1,
            time="",
            type=EventType.ANOMALY,
            flow="observer → reasoner",
            message=f"{len(risky_shipments)} shipments at elevated risk detected",
        )
        state.enqueue_event(ev)

    return output

