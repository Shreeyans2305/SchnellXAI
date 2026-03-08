import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from agents.graph import logistics_graph
from data.seed import empty_state, generate_sample_state, get_live_state, seed_state, set_live_state
from data.simulator import apply_disruption
from memory.short_term import short_term_memory

router = APIRouter()

_saved_scenario: dict = {
    "warehouses": [],
    "routes": [],
    "carriers": [],
    "shipments": [],
}


class ScenarioBody(BaseModel):
    warehouses: list = []
    routes: list = []
    carriers: list = []
    shipments: list = []


def _state_from_scenario(scenario: dict) -> dict:
    hubs = scenario.get("warehouses", scenario.get("hubs", []))
    return {
        "shipments": scenario.get("shipments", []),
        "hubs": hubs,
        "warehouses": hubs,
        "carriers": scenario.get("carriers", []),
        "routes": scenario.get("routes", []),
    }


def _build_cycle_state(state: dict) -> dict:
    return {
        "shipments": state.get("shipments", []),
        "hubs": state.get("warehouses", state.get("hubs", [])),
        "carriers": state.get("carriers", []),
        "observations": [],
        "hypotheses": [],
        "patterns_detected": [],
        "actions": [],
        "queued_approvals": [],
        "executed_actions": [],
        "lessons": [],
        "event_log": [],
        "observer_summary": "",
        "reasoner_summary": "",
        "decider_summary": "",
        "executor_summary": "",
        "learner_summary": "",
        "cycle_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/simulation/scenario")
def get_scenario():
    return _saved_scenario


@router.post("/simulation/scenario")
def save_scenario(body: ScenarioBody):
    global _saved_scenario
    _saved_scenario = body.model_dump()
    set_live_state(_state_from_scenario(_saved_scenario))
    return _saved_scenario


@router.post("/simulation/generate-sample")
def generate_sample():
    """Generate a pre-built sample logistics scenario for quick testing."""
    global _saved_scenario
    sample = generate_sample_state()
    _saved_scenario = {
        "warehouses": sample.get("hubs", []),
        "routes": sample.get("routes", []),
        "carriers": sample.get("carriers", []),
        "shipments": sample.get("shipments", []),
    }
    set_live_state(sample)
    return _saved_scenario


@router.post("/simulation/reset")
def reset_simulation():
    """Reset all simulation data to clean empty state."""
    global _saved_scenario
    _saved_scenario = {"warehouses": [], "routes": [], "carriers": [], "shipments": []}
    set_live_state(empty_state())
    short_term_memory._buffer.clear()
    return {"message": "All data reset to clean state.", "scenario": _saved_scenario}


@router.post("/simulation/run")
async def run_simulation(body: dict):
    _ = body
    state = _saved_scenario if _saved_scenario else get_live_state()
    cycle_state = _build_cycle_state(state)
    result = await logistics_graph.ainvoke(cycle_state)

    actions = result.get("actions", [])
    options = []
    for i, a in enumerate(actions[:3]):
        options.append(
            {
                "id": i + 1,
                "name": str(a.get("type", "action")).replace("_", " ").title(),
                "netScore": max(0, 100 - int(a.get("risk_score", 50))),
                "blastRadius": 2,
                "slaImpact": "+1h",
                "cost": f"+₹{int(a.get('cost_delta_inr', 0)):,}",
                "recommended": i == 0,
            }
        )

    if not options:
        options = [
            {
                "id": 1,
                "name": "No action required",
                "netScore": 95,
                "blastRadius": 0,
                "slaImpact": "0h",
                "cost": "₹0",
                "recommended": True,
            }
        ]

    return {
        "options": options,
        "cascadeImpact": [],
        "reasoning": f"{result.get('decider_summary', '')} {result.get('reasoner_summary', '')}".strip(),
    }


@router.post("/simulation/disruptions")
async def generate_disruption(body: dict):
    global _saved_scenario
    state = _state_from_scenario(_saved_scenario) if _saved_scenario else get_live_state()
    disrupted_state = apply_disruption(state, body)
    set_live_state(disrupted_state)

    _saved_scenario = {
        "warehouses": disrupted_state.get("hubs", []),
        "routes": disrupted_state.get("routes", []),
        "carriers": disrupted_state.get("carriers", []),
        "shipments": disrupted_state.get("shipments", []),
    }

    cycle_state = _build_cycle_state(disrupted_state)
    result = await logistics_graph.ainvoke(cycle_state)

    return {
        "message": f"Disruption '{body.get('type')}' applied and pipeline executed.",
        "scenario": _saved_scenario,
        "pipeline": {
            "observer": {"observations": result.get("observations", [])},
            "reasoner": {"hypotheses": result.get("hypotheses", [])},
            "decider": {"actions": result.get("actions", [])},
            "queuedApprovals": len(result.get("queued_approvals", [])),
        },
    }
