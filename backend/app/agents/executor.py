from __future__ import annotations

from typing import Tuple

from .base import AgentOutput
from ..models.domain import (
    ActionType,
    AgentAction,
    AgentEvent,
    CascadeImpact,
    EventType,
    ShipmentStatus,
)
from ..state import GlobalState


def _compute_combined_risk_metric(state: GlobalState) -> int:
    at_risk = len([s for s in state.shipments.values() if s.status == ShipmentStatus.AT_RISK])
    delayed = len([s for s in state.shipments.values() if s.status == ShipmentStatus.DELAYED])
    return at_risk + delayed


def _apply_action_to_state(state: GlobalState, action: AgentAction) -> Tuple[str, int, int]:
    """
    Mutate state in-place according to the selected action.

    Returns a tuple of (outcome_summary, before_metric, after_metric).
    """
    before_metric = _compute_combined_risk_metric(state)

    if action.type == ActionType.REROUTE_SHIPMENT and action.shipmentId:
        shipment = state.shipments.get(action.shipmentId)
        if shipment:
            # Simplified effect: reduce risk and improve status.
            shipment.risk = max(0, shipment.risk - 25)
            if shipment.risk <= 30:
                shipment.status = ShipmentStatus.ON_TRACK
                shipment.notes = "Reroute executed by Executor agent \u2014 back on track"
            else:
                shipment.status = ShipmentStatus.AT_RISK
                shipment.notes = "Reroute executed \u2014 still monitoring for delays"

    # Other action types could adjust carriers, hubs, etc.

    after_metric = _compute_combined_risk_metric(state)
    outcome = (
        f"Combined at-risk + delayed metric changed from {before_metric} to {after_metric} "
        f"after executing {action.type.value} on {action.shipmentId or 'N/A'}."
    )
    return outcome, before_metric, after_metric


async def run_executor(state: GlobalState, action: AgentAction) -> AgentOutput:
    """
    Executor: apply an approved or auto-executable action to the environment.
    """
    output = AgentOutput()

    outcome, before_metric, after_metric = _apply_action_to_state(state, action)
    output.explanation = outcome

    # Simple cascade impact: mark the primary shipment and a couple of neighbors.
    cascade = [
        CascadeImpact(
            shipment=action.shipmentId or "N/A",
            impact="Primary shipment affected by reroute",
            severity="medium",
        )
    ]
    output.cascade_impacts = cascade

    ev = AgentEvent(
        id=len(state.events) + 1,
        time="",
        type=EventType.EXECUTE,
        flow="executor \u2192 learner",
        message=outcome,
    )
    state.enqueue_event(ev)

    # Record in decision log; learner will consume this with additional context.
    state.decision_log.append(
        (
            action.id,
            action.description,
            f"{before_metric}->{after_metric}",
        )
    )

    return output

