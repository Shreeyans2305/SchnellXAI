from __future__ import annotations

import random
import re

from fastapi import APIRouter, HTTPException

from ..agents.orchestrator import (
    run_full_decision_with_action,
    run_observe_reason_decide_cycle,
    simulate_scenarios_for_shipment,
)
from ..models.domain import (
    AgentEvent,
    Carrier,
    DisruptionRequest,
    DisruptionResponse,
    EventType,
    Hub,
    LogisticsScenario,
    PipelineSummary,
    Shipment,
    ShipmentLocation,
    ShipmentStatus,
    SimulationRequest,
    SimulationResult,
)
from ..state import get_state


router = APIRouter(tags=["simulation"])


def _minutes_to_duration(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m:02d}m"


def _duration_to_minutes(value: str) -> int:
    m = re.search(r"(\d+)h\s*(\d+)m", value)
    if not m:
        return 180
    return (int(m.group(1)) * 60) + int(m.group(2))


def _build_scenario_from_state() -> LogisticsScenario:
    state = get_state()

    warehouses = [
        {
            "id": h.id,
            "name": h.name,
            "lat": h.lat,
            "lng": h.lng,
            "status": h.status,
        }
        for h in sorted(state.hubs.values(), key=lambda x: x.id)
    ]
    routes = list(state.logistics_routes.values())
    carriers = [
        {
            "id": c.id,
            "name": c.name,
            "reliability": c.reliability,
            "capacity": max(1, c.active + c.delayed),
        }
        for c in sorted(state.carriers.values(), key=lambda x: x.id)
    ]

    carrier_id_by_name = {c.name: c.id for c in state.carriers.values()}
    route_id_by_hubs = {
        (r["fromWarehouseId"], r["toWarehouseId"]): r["id"] for r in routes
    }
    hub_id_by_name = {h.name: h.id for h in state.hubs.values()}

    shipments = []
    for s in sorted(state.shipments.values(), key=lambda x: x.id):
        start_name, end_name = [x.strip() for x in s.route.split("→")]
        start_hub = hub_id_by_name.get(start_name + " Hub") or hub_id_by_name.get(start_name)
        end_hub = hub_id_by_name.get(end_name + " Hub") or hub_id_by_name.get(end_name)
        route_id = route_id_by_hubs.get((start_hub, end_hub)) if start_hub and end_hub else None
        if not route_id and routes:
            route_id = routes[0]["id"]

        shipments.append(
            {
                "id": s.id,
                "routeId": route_id or "",
                "carrierId": carrier_id_by_name.get(s.carrier, 1),
                "progress": s.progress,
                "risk": s.risk,
                "status": s.status,
                "slaMinutes": max(60, _duration_to_minutes(s.eta) + 120),
                "etaMinutes": max(30, _duration_to_minutes(s.eta)),
                "notes": s.notes,
            }
        )

    return LogisticsScenario(
        warehouses=warehouses,
        routes=routes,
        carriers=carriers,
        shipments=shipments,
    )


def _apply_scenario_to_state(scenario: LogisticsScenario) -> None:
    state = get_state()

    warehouse_ids = {w.id for w in scenario.warehouses}
    carrier_ids = {c.id for c in scenario.carriers}
    route_ids = {r.id for r in scenario.routes}

    if len(warehouse_ids) != len(scenario.warehouses):
        raise HTTPException(status_code=400, detail="Warehouse ids must be unique")
    if len(carrier_ids) != len(scenario.carriers):
        raise HTTPException(status_code=400, detail="Carrier ids must be unique")
    if len(route_ids) != len(scenario.routes):
        raise HTTPException(status_code=400, detail="Route ids must be unique")

    for route in scenario.routes:
        if route.fromWarehouseId not in warehouse_ids or route.toWarehouseId not in warehouse_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Route {route.id} references unknown warehouses",
            )

    state.hubs = {
        w.id: Hub(id=w.id, name=w.name, lat=w.lat, lng=w.lng, shipments=0, status=w.status)
        for w in scenario.warehouses
    }

    state.carriers = {
        c.id: Carrier(
            id=c.id,
            name=c.name,
            reliability=c.reliability,
            active=0,
            delayed=0,
            trend=[max(0, c.reliability - 3), c.reliability - 1, c.reliability],
            logo=(c.name[:2] or "CR").upper(),
        )
        for c in scenario.carriers
    }

    state.logistics_routes = {r.id: r.model_dump() for r in scenario.routes}

    state.shipments = {}
    state.shipment_locations = {}
    for s in scenario.shipments:
        if s.routeId not in route_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Shipment {s.id} references unknown route {s.routeId}",
            )
        if s.carrierId not in carrier_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Shipment {s.id} references unknown carrier {s.carrierId}",
            )

        route = state.logistics_routes[s.routeId]
        from_hub = state.hubs[route["fromWarehouseId"]]
        to_hub = state.hubs[route["toWarehouseId"]]
        carrier = state.carriers[s.carrierId]

        ratio = s.progress / 100.0
        lat = from_hub.lat + (to_hub.lat - from_hub.lat) * ratio
        lng = from_hub.lng + (to_hub.lng - from_hub.lng) * ratio

        route_name = f"{from_hub.name.replace(' Hub', '')} → {to_hub.name.replace(' Hub', '')}"
        state.shipments[s.id] = Shipment(
            id=s.id,
            route=route_name,
            carrier=carrier.name,
            progress=s.progress,
            eta=_minutes_to_duration(s.etaMinutes),
            sla=_minutes_to_duration(s.slaMinutes),
            risk=s.risk,
            agent="Observer",
            status=s.status,
            notes=s.notes,
        )
        state.shipment_locations[s.id] = ShipmentLocation(
            id=s.id,
            lat=lat,
            lng=lng,
            from_={"lat": from_hub.lat, "lng": from_hub.lng},
            to={"lat": to_hub.lat, "lng": to_hub.lng},
            status=s.status,
        )

        carrier.active += 1
        if s.status == ShipmentStatus.DELAYED:
            carrier.delayed += 1
        from_hub.shipments += 1
        to_hub.shipments += 1


def _pick_shipment(target_shipment_id: str | None):
    state = get_state()
    if target_shipment_id:
        shipment = state.shipments.get(target_shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Target shipment not found")
        return shipment
    if not state.shipments:
        raise HTTPException(status_code=400, detail="No shipments available")
    return max(state.shipments.values(), key=lambda s: s.risk)


def _apply_disruption(req: DisruptionRequest) -> str:
    state = get_state()
    severity = req.severity
    shipment = _pick_shipment(req.targetShipmentId)
    message = ""

    if req.type.value == "late_pickup":
        shipment.progress = max(0, shipment.progress - (severity // 4))
        shipment.risk = min(100, shipment.risk + max(10, severity // 2))
        shipment.status = ShipmentStatus.AT_RISK if severity < 80 else ShipmentStatus.DELAYED
        eta_minutes = _duration_to_minutes(shipment.eta) + max(30, severity)
        shipment.eta = _minutes_to_duration(eta_minutes)
        shipment.notes = f"Late pickup generated in simulation (severity={severity})"
        message = f"Late pickup generated for {shipment.id}"

    elif req.type.value == "warehouse_congestion":
        hub_id = req.targetWarehouseId
        if hub_id is None:
            if state.hubs:
                hub_id = random.choice(list(state.hubs.keys()))
            else:
                raise HTTPException(status_code=400, detail="No warehouses available")
        hub = state.hubs.get(hub_id)
        if not hub:
            raise HTTPException(status_code=404, detail="Target warehouse not found")
        hub.status = "congested"
        for s in state.shipments.values():
            if hub.name.replace(" Hub", "") in s.route:
                s.risk = min(100, s.risk + max(10, severity // 2))
                if s.risk > 80:
                    s.status = ShipmentStatus.DELAYED
        message = f"Warehouse congestion generated at {hub.name}"

    elif req.type.value == "inaccurate_eta":
        eta_minutes = _duration_to_minutes(shipment.eta) + max(45, severity)
        shipment.eta = _minutes_to_duration(eta_minutes)
        shipment.risk = min(100, shipment.risk + max(8, severity // 3))
        shipment.status = ShipmentStatus.AT_RISK
        shipment.notes = "ETA drift injected to test observer-reasoner detection"
        message = f"Inaccurate ETA generated for {shipment.id}"

    elif req.type.value == "cascading_reroute":
        impacted = [s for s in state.shipments.values() if s.carrier == shipment.carrier]
        for idx, s in enumerate(impacted):
            bump = max(6, severity // (idx + 2))
            s.risk = min(100, s.risk + bump)
            s.status = ShipmentStatus.AT_RISK if s.risk < 85 else ShipmentStatus.DELAYED
            s.notes = "Cascading reroute pressure propagated across same carrier lane"
        message = f"Cascading reroute generated for carrier {shipment.carrier}"

    state.enqueue_event(
        AgentEvent(
            id=len(state.events) + 1,
            time="",
            type=EventType.ALERT,
            flow="simulation → observer",
            message=message,
        )
    )
    return message


@router.get("/simulation/scenario", response_model=LogisticsScenario)
async def get_simulation_scenario():
    return _build_scenario_from_state()


@router.post("/simulation/scenario", response_model=LogisticsScenario)
async def upsert_simulation_scenario(scenario: LogisticsScenario):
    _apply_scenario_to_state(scenario)
    state = get_state()
    state.enqueue_event(
        AgentEvent(
            id=len(state.events) + 1,
            time="",
            type=EventType.OPTIMIZE,
            flow="simulation → state",
            message="Simulation scenario updated from UI builder",
        )
    )
    return _build_scenario_from_state()


@router.post("/simulation/disruptions", response_model=DisruptionResponse)
async def generate_disruption(req: DisruptionRequest):
    message = _apply_disruption(req)
    state = get_state()
    observer, reasoner, decider = await run_observe_reason_decide_cycle(state)
    await run_full_decision_with_action(state, auto_only=False)

    return DisruptionResponse(
        message=message,
        pipeline=PipelineSummary(
            observer=observer,
            reasoner=reasoner,
            decider=decider,
            queuedApprovals=len(state.approvals_queue),
        ),
    )


@router.post("/simulation/run", response_model=SimulationResult)
async def run_simulation(req: SimulationRequest):
    """
    Run a what-if simulation for a given shipment and hub without
    mutating live state.
    """
    state = get_state()
    return await simulate_scenarios_for_shipment(state, req)

