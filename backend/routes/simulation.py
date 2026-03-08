import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from agents.graph import logistics_graph
from data.seed import empty_state, generate_sample_state, get_live_state, seed_state, set_live_state
from data.simulator import apply_disruption
from memory.short_term import short_term_memory
from pipeline.buffer import anomaly_buffer
from pipeline.scheduler import pipeline_scheduler

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
    carriers = scenario.get("carriers", [])
    routes = scenario.get("routes", [])
    raw_shipments = scenario.get("shipments", [])

    # Build lookup maps for resolving references
    hub_by_id = {int(h["id"]): h for h in hubs if "id" in h}
    carrier_by_id = {int(c["id"]): c for c in carriers if "id" in c}
    route_by_id = {r["id"]: r for r in routes if "id" in r}

    sla_labels = ["Standard", "Express", "Priority", "Economy"]

    enriched_shipments = []
    for s in raw_shipments:
        s = dict(s)  # shallow copy to avoid mutating the original

        # ── Resolve route display string ──
        if not s.get("route") and s.get("routeId"):
            rte = route_by_id.get(s["routeId"])
            if rte:
                frm = hub_by_id.get(int(rte.get("fromWarehouseId", 0)), {})
                to = hub_by_id.get(int(rte.get("toWarehouseId", 0)), {})
                frm_name = frm.get("name", "Origin").replace(" Hub", "")
                to_name = to.get("name", "Destination").replace(" Hub", "")
                s["route"] = f"{frm_name} \u2192 {to_name}"

        # ── Resolve carrier name ──
        if not s.get("carrier") and s.get("carrierId"):
            cr = carrier_by_id.get(int(s["carrierId"]), {})
            s["carrier"] = cr.get("name", "Unknown")

        # ── Format ETA string ──
        if not s.get("eta") and s.get("etaMinutes") is not None:
            mins = int(s["etaMinutes"])
            s["eta"] = f"{mins // 60}h {mins % 60}m"
        elif not s.get("eta"):
            s["eta"] = "—"

        # ── Resolve SLA label ──
        if not s.get("sla"):
            if s.get("slaMinutes") is not None:
                sla_m = int(s["slaMinutes"])
                if sla_m <= 180:
                    s["sla"] = "Priority"
                elif sla_m <= 360:
                    s["sla"] = "Express"
                elif sla_m <= 600:
                    s["sla"] = "Standard"
                else:
                    s["sla"] = "Economy"
            else:
                s["sla"] = "Standard"

        # ── Defaults ──
        s.setdefault("agent", "\u2014")
        s.setdefault("status", "ON TRACK")
        s.setdefault("progress", 0)
        s.setdefault("risk", 0)
        s.setdefault("notes", "")

        enriched_shipments.append(s)

    return {
        "shipments": enriched_shipments,
        "hubs": hubs,
        "warehouses": hubs,
        "carriers": carriers,
        "routes": routes,
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
        "buffered_anomalies": [],
        "anomaly_history": [],
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

    # Buffer the anomaly instead of running the pipeline inline.
    # The scheduler will pick it up in the next cycle (within ~25s).
    anomaly_buffer.push(body)

    return {
        "message": (
            f"Disruption '{body.get('type')}' applied and buffered. "
            f"Pipeline will process {anomaly_buffer.count} queued anomalies in the next cycle."
        ),
        "scenario": _saved_scenario,
        "buffered_count": anomaly_buffer.count,
        "pipeline": pipeline_scheduler.last_cycle,
    }


@router.get("/simulation/pipeline-status")
def pipeline_status():
    """Return the current pipeline scheduler status and latest cycle results."""
    return pipeline_scheduler.status()


@router.get("/simulation/anomaly-buffer")
def anomaly_buffer_peek():
    """Peek at currently buffered anomalies waiting for the next cycle."""
    return {
        "count": anomaly_buffer.count,
        "anomalies": anomaly_buffer.peek(),
    }


@router.get("/simulation/anomaly-history")
def anomaly_history(limit: int = 50):
    """Return recent anomalies from the long-term anomaly log."""
    return anomaly_buffer.recent_history(limit)
