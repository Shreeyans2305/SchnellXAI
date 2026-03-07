from __future__ import annotations

import asyncio
import random
from typing import Tuple

from .decider import run_decider
from .executor import run_executor
from .observer import run_observer
from .reasoner import run_reasoner
from .learner import run_learner
from ..config import settings
from ..data import seed_state
from ..models.domain import (
    Approval,
    CascadeImpact,
    DashboardMetrics,
    MetricValue,
    ShipmentStatus,
    SimulationOption,
    SimulationRequest,
    SimulationResult,
)
from ..state import GlobalState


def _recompute_metrics(state: GlobalState) -> None:
    shipments = list(state.shipments.values())
    at_risk = len([s for s in shipments if s.status == ShipmentStatus.AT_RISK])
    delayed = len([s for s in shipments if s.status == ShipmentStatus.DELAYED])

    agent_ops_prev = state.metrics.agentOps.value if state.metrics else 0  # type: ignore[union-attr]
    approvals_prev = state.metrics.approvals.value if state.metrics else 0  # type: ignore[union-attr]

    state.metrics = DashboardMetrics(
        shipments=MetricValue(value=len(shipments), change="+0%"),
        atRisk=MetricValue(value=at_risk, change="+0"),
        delayed=MetricValue(value=delayed, change="+0"),
        agentOps=MetricValue(value=agent_ops_prev + 1, change="+1"),
        approvals=MetricValue(value=approvals_prev, change="+0"),
        ollamaStatus="connected",
        agentsActive=len(state.agents),
        agentsTotal=len(state.agents),
    )


async def run_observe_reason_decide_cycle(
    state: GlobalState,
) -> Tuple[dict, dict, dict]:
    """
    Run a single observe → reason → decide cycle and return summaries.
    """
    observer_out = await run_observer(state)
    reasoner_out = await run_reasoner(state, observer_out)
    decider_out = await run_decider(state, observer_out, reasoner_out)

    return (
        observer_out.__dict__,
        reasoner_out.__dict__,
        decider_out.__dict__,
    )


async def run_full_decision_with_action(
    state: GlobalState, auto_only: bool = True
) -> None:
    """
    Run the full observe → reason → decide → act → learn loop once.

    - Auto-executable actions are immediately executed.
    - Actions requiring approval are converted into Approval objects and queued.
    """
    from ..models.domain import AgentAction  # local import to avoid cycles

    observer_out = await run_observer(state)
    reasoner_out = await run_reasoner(state, observer_out)
    decider_out = await run_decider(state, observer_out, reasoner_out)

    for action in decider_out.actions:
        assert isinstance(action, AgentAction)
        if action.requiresApproval and not auto_only:
            # Create an Approval proposal for human review.
            shipment = state.shipments.get(action.shipmentId or "")
            current_route = shipment.route.split(" \u2192 ") if shipment else []
            proposed_route = current_route[:]
            if "Nagpur" in (shipment.notes if shipment else "") and "Pune" not in proposed_route:
                proposed_route = ["Mumbai", "Pune", "Bhopal", "Delhi"]

            approval = Approval(
                id=f"APR-{action.shipmentId}",
                shipmentId=action.shipmentId or "",
                action=action.description,
                currentRoute=current_route or ["Mumbai", "Nagpur", "Delhi"],
                proposedRoute=proposed_route or ["Mumbai", "Pune", "Bhopal", "Delhi"],
                blastRadius=action.blastRadius,
                netScore=82,
                costDelta=f"+\u20b9{int(action.costDelta)}",
                slaImpact=f"+{action.slaImpactMinutes // 60}h",
                reason=decider_out.explanation
                or "Multi-agent evaluation recommends this reroute under current congestion.",
            )
            state.enqueue_approval(approval)

            if state.metrics:
                state.metrics.approvals.value += 1
        else:
            # Auto-execute permissible actions.
            await run_executor(state, action)
            await run_learner(state)

    _recompute_metrics(state)


async def run_simulation_loop_forever(state: GlobalState) -> None:
    """
    Background loop that advances shipment progress and positions,
    and injects occasional delays / congestion.
    """
    try:
        while True:
            for loc in state.shipment_locations.values():
                shipment = state.shipments.get(loc.id)
                if not shipment:
                    continue
                # Advance progress a bit towards completion
                if shipment.progress < 100:
                    shipment.progress = min(100, shipment.progress + random.randint(1, 4))
                # Interpolate map position based on progress
                ratio = shipment.progress / 100.0
                loc.lat = loc.from_.lat + (loc.to.lat - loc.from_.lat) * ratio
                loc.lng = loc.from_.lng + (loc.to.lng - loc.from_.lng) * ratio

                # Occasionally inject delays or clear them
                if random.random() < 0.05:
                    shipment.status = ShipmentStatus.DELAYED
                    shipment.risk = min(100, shipment.risk + 10)
                elif shipment.status == ShipmentStatus.DELAYED and random.random() < 0.1:
                    shipment.status = ShipmentStatus.ON_TRACK
                    shipment.risk = max(0, shipment.risk - 20)

            # Toggle hub congestion randomly to keep the map interesting
            for hub in state.hubs.values():
                if random.random() < 0.02:
                    hub.status = "congested" if hub.status == "active" else "active"

            _recompute_metrics(state)

            await asyncio.sleep(settings.simulation_tick_seconds)
    except asyncio.CancelledError:
        # Graceful shutdown
        return


async def run_agent_cycle_forever(state: GlobalState) -> None:
    """
    Background loop running the full multi-agent pipeline periodically.
    """
    try:
        # Ensure state is seeded if not already
        if not state.shipments:
            seed_state(state)

        while True:
            await run_full_decision_with_action(state, auto_only=False)
            await asyncio.sleep(settings.simulation_tick_seconds * 2)
    except asyncio.CancelledError:
        return


async def simulate_scenarios_for_shipment(
    state: GlobalState, req: SimulationRequest
) -> SimulationResult:
    """
    Create a SimulationResult for the given shipment and hub without
    mutating the live state.
    """
    shipment = state.shipments.get(req.shipmentId)
    if not shipment:
        # Fallback: generic options
        options = [
            SimulationOption(
                id=1,
                name=f"Reroute via {req.hub}",
                netScore=80,
                blastRadius=3,
                slaImpact="+2h",
                cost="+\u20b92,400",
                recommended=True,
            ),
            SimulationOption(
                id=2,
                name="Keep current route",
                netScore=50,
                blastRadius=1,
                slaImpact="+4h",
                cost="\u20b90",
                recommended=False,
            ),
        ]
    else:
        options = [
            SimulationOption(
                id=1,
                name=f"Reroute {shipment.id} via {req.hub}",
                netScore=82,
                blastRadius=3,
                slaImpact="+2h",
                cost="+\u20b92,400",
                recommended=True,
            ),
            SimulationOption(
                id=2,
                name="Alternate high-capacity route",
                netScore=68,
                blastRadius=5,
                slaImpact="+4h",
                cost="+\u20b94,100",
                recommended=False,
            ),
            SimulationOption(
                id=3,
                name="Wait for congestion to clear",
                netScore=45,
                blastRadius=8,
                slaImpact="+6h",
                cost="\u20b90",
                recommended=False,
            ),
        ]

    cascade = [
        CascadeImpact(
            shipment=req.shipmentId,
            impact="Primary \u2014 rerouted in simulation",
            severity="medium",
        )
    ]

    reasoning = (
        "The Observer detected risk signals on the selected shipment and nearby hubs. "
        "The Reasoner compared historical outcomes for alternative hubs, and the Decider "
        "evaluated three options against SLA impact, cost, and blast radius. "
        "The recommended option balances moderate SLA impact with a limited blast radius."
    )

    return SimulationResult(options=options, cascadeImpact=cascade, reasoning=reasoning)

