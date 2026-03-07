"""Data seeding and shared in-memory logistics state."""

import copy
import random
from threading import Lock

HUBS = [
    {
        "id": i + 1,
        "name": n,
        "lat": la,
        "lng": ln,
        "shipments": random.randint(60, 350),
        "status": s,
    }
    for i, (n, la, ln, s) in enumerate(
        [
            ("Mumbai Hub", 19.076, 72.877, "active"),
            ("Delhi Hub", 28.704, 77.102, "active"),
            ("Bangalore Hub", 12.971, 77.594, "active"),
            ("Chennai Hub", 13.082, 80.270, "active"),
            ("Kolkata Hub", 22.572, 88.363, "active"),
            ("Hyderabad Hub", 17.385, 78.486, "active"),
            ("Pune Hub", 18.520, 73.856, "active"),
            ("Ahmedabad Hub", 23.022, 72.571, "active"),
            ("Jaipur Hub", 26.912, 75.787, "active"),
            ("Lucknow Hub", 26.846, 80.946, "active"),
            ("Nagpur Hub", 21.145, 79.088, "congested"),
            ("Bhopal Hub", 23.259, 77.412, "active"),
        ]
    )
]

CARRIERS = [
    {"id": 1, "name": "BlueDart", "reliability": 94, "active": 342, "delayed": 12},
    {"id": 2, "name": "Delhivery", "reliability": 91, "active": 287, "delayed": 18},
    {"id": 3, "name": "DTDC", "reliability": 87, "active": 198, "delayed": 24},
    {"id": 4, "name": "XpressBees", "reliability": 89, "active": 156, "delayed": 15},
    {"id": 5, "name": "Shadowfax", "reliability": 85, "active": 134, "delayed": 20},
]


def _make_shipment(idx: int) -> dict:
    routes = [
        ("Mumbai", "Delhi", "BlueDart"),
        ("Chennai", "Kolkata", "Delhivery"),
        ("Bangalore", "Hyderabad", "BlueDart"),
        ("Delhi", "Jaipur", "DTDC"),
        ("Pune", "Ahmedabad", "XpressBees"),
        ("Kolkata", "Lucknow", "Shadowfax"),
        ("Hyderabad", "Chennai", "Delhivery"),
        ("Ahmedabad", "Mumbai", "DTDC"),
    ]
    frm, to, carrier = routes[idx % len(routes)]
    progress = random.randint(5, 95)
    risk = random.randint(5, 95)
    status = "DELAYED" if risk > 80 else "AT RISK" if risk > 55 else "ON TRACK"
    eta_minutes = int((100 - progress) / 100 * random.randint(60, 480))
    return {
        "id": f"SHP-{4000 + idx * 37}",
        "route": f"{frm} → {to}",
        "carrier": carrier,
        "progress": progress,
        "eta": f"{eta_minutes // 60}h {eta_minutes % 60}m",
        "sla": random.choice(["Standard", "Express", "Priority", "Economy"]),
        "risk": risk,
        "agent": random.choice(["Observer", "Reasoner", "Decider", "Executor"]),
        "status": status,
        "notes": "Auto-generated shipment",
    }


def seed_state(n_shipments: int = 8) -> dict:
    return {
        "shipments": [_make_shipment(i) for i in range(n_shipments)],
        "hubs": copy.deepcopy(HUBS),
        "carriers": copy.deepcopy(CARRIERS),
    }


def empty_state() -> dict:
    """Return a clean empty state with no data."""
    return {"shipments": [], "hubs": [], "carriers": []}


def generate_sample_state() -> dict:
    """Generate a realistic sample logistics scenario for demo/testing."""
    sample_hubs = [
        {"id": 1, "name": "Mumbai Hub", "lat": 19.076, "lng": 72.877, "shipments": 0, "status": "active"},
        {"id": 2, "name": "Delhi Hub", "lat": 28.704, "lng": 77.102, "shipments": 0, "status": "active"},
        {"id": 3, "name": "Bangalore Hub", "lat": 12.971, "lng": 77.594, "shipments": 0, "status": "active"},
        {"id": 4, "name": "Chennai Hub", "lat": 13.082, "lng": 80.270, "shipments": 0, "status": "active"},
        {"id": 5, "name": "Kolkata Hub", "lat": 22.572, "lng": 88.363, "shipments": 0, "status": "active"},
        {"id": 6, "name": "Pune Hub", "lat": 18.520, "lng": 73.856, "shipments": 0, "status": "active"},
        {"id": 7, "name": "Nagpur Hub", "lat": 21.145, "lng": 79.088, "shipments": 0, "status": "active"},
        {"id": 8, "name": "Hyderabad Hub", "lat": 17.385, "lng": 78.486, "shipments": 0, "status": "active"},
    ]
    sample_carriers = [
        {"id": 1, "name": "BlueDart", "reliability": 94, "capacity": 350},
        {"id": 2, "name": "Delhivery", "reliability": 91, "capacity": 300},
        {"id": 3, "name": "DTDC", "reliability": 87, "capacity": 220},
    ]
    sample_routes = [
        {"id": "RTE-1001", "fromWarehouseId": 1, "toWarehouseId": 2, "distanceKm": 1410, "typicalEtaMinutes": 420},
        {"id": "RTE-1002", "fromWarehouseId": 3, "toWarehouseId": 4, "distanceKm": 350, "typicalEtaMinutes": 150},
        {"id": "RTE-1003", "fromWarehouseId": 1, "toWarehouseId": 7, "distanceKm": 830, "typicalEtaMinutes": 260},
        {"id": "RTE-1004", "fromWarehouseId": 7, "toWarehouseId": 2, "distanceKm": 1030, "typicalEtaMinutes": 330},
        {"id": "RTE-1005", "fromWarehouseId": 6, "toWarehouseId": 8, "distanceKm": 560, "typicalEtaMinutes": 200},
        {"id": "RTE-1006", "fromWarehouseId": 5, "toWarehouseId": 2, "distanceKm": 1500, "typicalEtaMinutes": 480},
    ]
    route_data = [
        ("RTE-1001", 1, "Mumbai \u2192 Delhi", "BlueDart"),
        ("RTE-1002", 2, "Bangalore \u2192 Chennai", "Delhivery"),
        ("RTE-1003", 1, "Mumbai \u2192 Nagpur", "BlueDart"),
        ("RTE-1004", 3, "Nagpur \u2192 Delhi", "DTDC"),
        ("RTE-1005", 2, "Pune \u2192 Hyderabad", "Delhivery"),
        ("RTE-1006", 3, "Kolkata \u2192 Delhi", "DTDC"),
    ]
    sample_shipments = []
    for i, (route_id, carrier_id, route_label, carrier_name) in enumerate(route_data):
        progress = random.randint(10, 85)
        risk = random.randint(10, 50)
        status = "ON TRACK" if risk < 40 else "AT RISK"
        eta_minutes = int((100 - progress) / 100 * random.randint(120, 480))
        sample_shipments.append({
            "id": f"SHP-{5000 + i * 111}",
            "routeId": route_id,
            "carrierId": carrier_id,
            "route": route_label,
            "carrier": carrier_name,
            "progress": progress,
            "eta": f"{eta_minutes // 60}h {eta_minutes % 60}m",
            "sla": random.choice(["Standard", "Express", "Priority"]),
            "risk": risk,
            "agent": "—",
            "status": status,
            "notes": "Sample shipment — run disruptions to test the AI agents",
        })
    return {
        "shipments": sample_shipments,
        "hubs": sample_hubs,
        "carriers": sample_carriers,
        "routes": sample_routes,
        "warehouses": sample_hubs,
    }


_state_lock = Lock()
_live_state: dict = empty_state()


def get_live_state() -> dict:
    with _state_lock:
        return copy.deepcopy(_live_state)


def set_live_state(state: dict) -> dict:
    global _live_state
    with _state_lock:
        _live_state = copy.deepcopy(state)
        return copy.deepcopy(_live_state)


def reset_live_state() -> dict:
    global _live_state
    with _state_lock:
        _live_state = seed_state()
        return copy.deepcopy(_live_state)
