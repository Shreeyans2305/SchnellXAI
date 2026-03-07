from __future__ import annotations

from datetime import datetime

from ..models.domain import (
    Agent,
    AgentEdge,
    AgentEvent,
    Carrier,
    DashboardMetrics,
    EventType,
    Hub,
    MetricValue,
    Shipment,
    ShipmentLocation,
    ShipmentStatus,
)
from ..state import GlobalState


def _now_time_str() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def seed_state(state: GlobalState) -> None:
    """Seed the in-memory state with demo data aligned to the frontend mocks."""

    # Shipments
    shipments = [
        Shipment(
            id="SHP-4821",
            route="Mumbai \u2192 Delhi",
            carrier="BlueDart",
            progress=45,
            eta="2h 30m",
            sla="Standard",
            risk=78,
            agent="Decider",
            status=ShipmentStatus.AT_RISK,
            notes="Nagpur hub congestion \u2014 reroute pending approval",
        ),
        Shipment(
            id="SHP-3192",
            route="Chennai \u2192 Kolkata",
            carrier="Delhivery",
            progress=72,
            eta="1h 15m",
            sla="Express",
            risk=25,
            agent="Executor",
            status=ShipmentStatus.ON_TRACK,
            notes="Rerouted via Pune \u2014 on schedule",
        ),
        Shipment(
            id="SHP-7734",
            route="Bangalore \u2192 Hyderabad",
            carrier="BlueDart",
            progress=30,
            eta="4h 00m",
            sla="Standard",
            risk=92,
            agent="Observer",
            status=ShipmentStatus.DELAYED,
            notes="Carrier delay at Nagpur \u2014 awaiting update",
        ),
        Shipment(
            id="SHP-5567",
            route="Delhi \u2192 Jaipur",
            carrier="DTDC",
            progress=88,
            eta="0h 45m",
            sla="Priority",
            risk=15,
            agent="Executor",
            status=ShipmentStatus.ON_TRACK,
            notes="Final mile delivery in progress",
        ),
        Shipment(
            id="SHP-9023",
            route="Pune \u2192 Ahmedabad",
            carrier="XpressBees",
            progress=55,
            eta="3h 10m",
            sla="Standard",
            risk=45,
            agent="Reasoner",
            status=ShipmentStatus.AT_RISK,
            notes="Weather advisory on route \u2014 monitoring",
        ),
        Shipment(
            id="SHP-1156",
            route="Kolkata \u2192 Lucknow",
            carrier="Shadowfax",
            progress=20,
            eta="5h 20m",
            sla="Economy",
            risk=60,
            agent="Observer",
            status=ShipmentStatus.AT_RISK,
            notes="High traffic on NH2 \u2014 alternate route analysis",
        ),
        Shipment(
            id="SHP-6640",
            route="Hyderabad \u2192 Chennai",
            carrier="Delhivery",
            progress=95,
            eta="0h 20m",
            sla="Express",
            risk=5,
            agent="Executor",
            status=ShipmentStatus.ON_TRACK,
            notes="Arriving at destination hub",
        ),
        Shipment(
            id="SHP-8312",
            route="Ahmedabad \u2192 Mumbai",
            carrier="DTDC",
            progress=10,
            eta="6h 00m",
            sla="Standard",
            risk=85,
            agent="Decider",
            status=ShipmentStatus.DELAYED,
            notes="Vehicle breakdown \u2014 replacement dispatched",
        ),
    ]
    state.shipments = {s.id: s for s in shipments}

    # Carriers
    carriers = [
        Carrier(
            id=1,
            name="BlueDart",
            reliability=94,
            active=342,
            delayed=12,
            trend=[88, 90, 91, 93, 94, 92, 94],
            logo="BD",
        ),
        Carrier(
            id=2,
            name="Delhivery",
            reliability=91,
            active=287,
            delayed=18,
            trend=[85, 87, 89, 90, 91, 89, 91],
            logo="DL",
        ),
        Carrier(
            id=3,
            name="DTDC",
            reliability=87,
            active=198,
            delayed=24,
            trend=[82, 84, 85, 86, 87, 88, 87],
            logo="DT",
        ),
        Carrier(
            id=4,
            name="XpressBees",
            reliability=89,
            active=156,
            delayed=15,
            trend=[84, 86, 87, 88, 89, 90, 89],
            logo="XB",
        ),
        Carrier(
            id=5,
            name="Shadowfax",
            reliability=85,
            active=134,
            delayed=20,
            trend=[80, 82, 83, 84, 85, 84, 85],
            logo="SF",
        ),
    ]
    state.carriers = {c.id: c for c in carriers}

    # Hubs
    hubs = [
        Hub(
            id=1,
            name="Mumbai Hub",
            lat=19.076,
            lng=72.8777,
            shipments=342,
            status="active",
        ),
        Hub(
            id=2,
            name="Delhi Hub",
            lat=28.7041,
            lng=77.1025,
            shipments=287,
            status="active",
        ),
        Hub(
            id=3,
            name="Bangalore Hub",
            lat=12.9716,
            lng=77.5946,
            shipments=198,
            status="active",
        ),
        Hub(
            id=4,
            name="Chennai Hub",
            lat=13.0827,
            lng=80.2707,
            shipments=156,
            status="active",
        ),
        Hub(
            id=5,
            name="Kolkata Hub",
            lat=22.5726,
            lng=88.3639,
            shipments=134,
            status="active",
        ),
        Hub(
            id=6,
            name="Hyderabad Hub",
            lat=17.385,
            lng=78.4867,
            shipments=178,
            status="active",
        ),
        Hub(
            id=7,
            name="Pune Hub",
            lat=18.5204,
            lng=73.8567,
            shipments=145,
            status="active",
        ),
        Hub(
            id=8,
            name="Ahmedabad Hub",
            lat=23.0225,
            lng=72.5714,
            shipments=112,
            status="active",
        ),
        Hub(
            id=9,
            name="Jaipur Hub",
            lat=26.9124,
            lng=75.7873,
            shipments=89,
            status="active",
        ),
        Hub(
            id=10,
            name="Lucknow Hub",
            lat=26.8467,
            lng=80.9462,
            shipments=95,
            status="active",
        ),
        Hub(
            id=11,
            name="Nagpur Hub",
            lat=21.1458,
            lng=79.0882,
            shipments=167,
            status="congested",
        ),
        Hub(
            id=12,
            name="Bhopal Hub",
            lat=23.2599,
            lng=77.4126,
            shipments=78,
            status="active",
        ),
    ]
    state.hubs = {h.id: h for h in hubs}

    # Editable logistics routes used by simulation builder UI.
    state.logistics_routes = {
        "RTE-1001": {
            "id": "RTE-1001",
            "fromWarehouseId": 1,
            "toWarehouseId": 2,
            "distanceKm": 1410.0,
            "typicalEtaMinutes": 420,
        },
        "RTE-1002": {
            "id": "RTE-1002",
            "fromWarehouseId": 4,
            "toWarehouseId": 5,
            "distanceKm": 1660.0,
            "typicalEtaMinutes": 540,
        },
        "RTE-1003": {
            "id": "RTE-1003",
            "fromWarehouseId": 3,
            "toWarehouseId": 6,
            "distanceKm": 570.0,
            "typicalEtaMinutes": 240,
        },
        "RTE-1004": {
            "id": "RTE-1004",
            "fromWarehouseId": 2,
            "toWarehouseId": 9,
            "distanceKm": 280.0,
            "typicalEtaMinutes": 90,
        },
        "RTE-1005": {
            "id": "RTE-1005",
            "fromWarehouseId": 7,
            "toWarehouseId": 8,
            "distanceKm": 660.0,
            "typicalEtaMinutes": 190,
        },
    }

    # Shipment locations (for map)
    shipment_locations = [
        ShipmentLocation(
            id="SHP-4821",
            lat=20.5,
            lng=76.5,
            from_={"lat": 19.076, "lng": 72.8777},
            to={"lat": 28.7041, "lng": 77.1025},
            status=ShipmentStatus.AT_RISK,
        ),
        ShipmentLocation(
            id="SHP-3192",
            lat=17.5,
            lng=80.0,
            from_={"lat": 13.0827, "lng": 80.2707},
            to={"lat": 22.5726, "lng": 88.3639},
            status=ShipmentStatus.ON_TRACK,
        ),
        ShipmentLocation(
            id="SHP-7734",
            lat=15.0,
            lng=78.0,
            from_={"lat": 12.9716, "lng": 77.5946},
            to={"lat": 17.385, "lng": 78.4867},
            status=ShipmentStatus.DELAYED,
        ),
        ShipmentLocation(
            id="SHP-5567",
            lat=27.5,
            lng=76.5,
            from_={"lat": 28.7041, "lng": 77.1025},
            to={"lat": 26.9124, "lng": 75.7873},
            status=ShipmentStatus.ON_TRACK,
        ),
        ShipmentLocation(
            id="SHP-9023",
            lat=20.5,
            lng=73.5,
            from_={"lat": 18.5204, "lng": 73.8567},
            to={"lat": 23.0225, "lng": 72.5714},
            status=ShipmentStatus.AT_RISK,
        ),
    ]
    state.shipment_locations = {loc.id: loc for loc in shipment_locations}

    # Agent mesh (fixed roles)
    agents = [
        Agent(
            id="observer",
            name="Observer",
            status="active",
            load=72,
            messagesProcessed=3421,
            lastAction="Scanning Nagpur hub telemetry",
            color="#60a5fa",
        ),
        Agent(
            id="reasoner",
            name="Reasoner",
            status="active",
            load=58,
            messagesProcessed=2180,
            lastAction="Analyzing delay correlation patterns",
            color="#c084fc",
        ),
        Agent(
            id="decider",
            name="Decider",
            status="active",
            load=45,
            messagesProcessed=1842,
            lastAction="Evaluating reroute for SHP-4821",
            color="#f5a623",
        ),
        Agent(
            id="executor",
            name="Executor",
            status="active",
            load=63,
            messagesProcessed=1567,
            lastAction="Dispatching manifest to Delhivery",
            color="#4ade80",
        ),
        Agent(
            id="learner",
            name="Learner",
            status="active",
            load=34,
            messagesProcessed=980,
            lastAction="Updating route optimization model",
            color="#f87171",
        ),
    ]
    state.agents = {a.id: a for a in agents}

    edges = [
        AgentEdge(from_="observer", to="reasoner", active=True),
        AgentEdge(from_="observer", to="decider", active=False),
        AgentEdge(from_="reasoner", to="decider", active=True),
        AgentEdge(from_="reasoner", to="executor", active=False),
        AgentEdge(from_="decider", to="executor", active=True),
        AgentEdge(from_="executor", to="learner", active=True),
        AgentEdge(from_="learner", to="observer", active=False),
        AgentEdge(from_="learner", to="reasoner", active=True),
    ]
    state.agent_edges = edges

    # Initial events similar to frontend mock
    events = [
        AgentEvent(
            id=1,
            time=_now_time_str(),
            type=EventType.ANOMALY,
            flow="observer \u2192 reasoner",
            message="SHP-4821 Nagpur hub throughput drop \u221234%",
        ),
        AgentEvent(
            id=2,
            time=_now_time_str(),
            type=EventType.REROUTE,
            flow="decider \u2192 executor",
            message="SHP-3192 rerouted via Pune Hub \u2014 ETA adjusted +2h",
        ),
    ]
    for ev in events:
        state.enqueue_event(ev)

    # Initial dashboard metrics
    state.metrics = DashboardMetrics(
        shipments=MetricValue(value=len(shipments), change="+0%"),
        atRisk=MetricValue(
            value=len([s for s in shipments if s.status == ShipmentStatus.AT_RISK]),
            change="+0",
        ),
        delayed=MetricValue(
            value=len([s for s in shipments if s.status == ShipmentStatus.DELAYED]),
            change="+0",
        ),
        agentOps=MetricValue(value=14520, change="+0"),
        approvals=MetricValue(value=1, change="+0"),
        ollamaStatus="connected",
        agentsActive=len(agents),
        agentsTotal=len(agents),
    )

