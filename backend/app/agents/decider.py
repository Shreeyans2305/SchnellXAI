from __future__ import annotations

from typing import List

from .base import AgentOutput, call_gemma_structured
from ..config import settings
from ..models.domain import ActionType, AgentAction, AgentEvent, EventType, Shipment
from ..state import GlobalState


def _heuristic_actions(state: GlobalState, risky_shipments: List[Shipment]) -> List[AgentAction]:
    actions: List[AgentAction] = []
    for s in risky_shipments:
        # Blast radius approximated by number of other shipments on same carrier
        blast_radius = len(
            [x for x in state.shipments.values() if x.carrier == s.carrier]
        )
        cost_delta = 2400.0 if "Nagpur" in s.notes or "congestion" in s.notes else 1200.0
        requires_approval = (
            blast_radius > settings.auto_execute_max_blast_radius
            or cost_delta > settings.auto_execute_max_cost_delta
        )

        action = AgentAction(
            id=f"ACT-{s.id}",
            type=ActionType.REROUTE_SHIPMENT,
            shipmentId=s.id,
            description=f"Reroute {s.id} away from congested hub or degraded carrier",
            blastRadius=blast_radius,
            costDelta=cost_delta,
            slaImpactMinutes=120,
            requiresApproval=requires_approval,
            recommended=True,
            rationale="Heuristic: high risk score and congestion indicators",
        )
        actions.append(action)
    return actions


async def run_decider(
    state: GlobalState, observer_output: AgentOutput, reasoner_output: AgentOutput
) -> AgentOutput:
    """
    Decider: propose concrete actions under configured guardrails.
    """
    output = AgentOutput()

    risky_ids = {
        item["id"]
        for obs in observer_output.observations
        if obs["type"] == "risky_shipments"
        for item in obs["items"]
    }
    risky_shipments = [s for s in state.shipments.values() if s.id in risky_ids]

    actions = _heuristic_actions(state, risky_shipments)

    # Optionally refine scoring or rationale via Gemma
    if actions:
        system = (
            "You are a logistics decision-maker. Given candidate actions, "
            "rate them qualitatively and explain the trade-offs."
        )
        user = f"Candidate actions: {[a.model_dump() for a in actions]}\n"
        struct = await call_gemma_structured(system, user)
        if isinstance(struct, dict) and "explanation" in struct:
            output.explanation = str(struct["explanation"])

    output.actions = actions

    if actions:
        ev_type = EventType.APPROVAL
        message = f"{len(actions)} candidate interventions generated; some may require approval"
        ev = AgentEvent(
            id=len(state.events) + 1,
            time="",
            type=ev_type,
            flow="decider → executor",
            message=message,
        )
        state.enqueue_event(ev)

    return output

