"""Injects realistic disruptions into a scenario state."""

import random

DISRUPTION_HANDLERS = {}


def disruption(name):
    def decorator(fn):
        DISRUPTION_HANDLERS[name] = fn
        return fn

    return decorator


@disruption("late_pickup")
def late_pickup(state: dict, payload: dict) -> dict:
    target = payload.get("targetShipmentId")
    severity = payload.get("severity", 60)
    for s in state.get("shipments", []):
        if s.get("id") == target or target is None:
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 2)
            s["status"] = "DELAYED"
            s["notes"] = f"Late pickup detected — severity {severity}"
    return state


@disruption("hub_congestion")
def hub_congestion(state: dict, payload: dict) -> dict:
    hub_id = payload.get("targetWarehouseId") or payload.get("targetHubId")
    hubs = state.get("hubs") or state.get("warehouses", [])
    for h in hubs:
        if str(h.get("id")) == str(hub_id):
            h["status"] = "congested"
            h["shipments"] = min(int(h.get("shipments", 120)) + random.randint(40, 120), 600)
    for s in state.get("shipments", []):
        s["risk"] = min(100, int(s.get("risk", 30)) + 20)
        if s["risk"] >= 80:
            s["status"] = "DELAYED"
        elif s["risk"] >= 55:
            s["status"] = "AT RISK"
    return state


@disruption("carrier_degradation")
def carrier_degradation(state: dict, payload: dict) -> dict:
    target = payload.get("targetShipmentId")
    severity = payload.get("severity", 50)
    for s in state.get("shipments", []):
        if s.get("id") == target or target is None:
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 3)
            if s["risk"] >= 80:
                s["status"] = "DELAYED"
            elif s["risk"] >= 55:
                s["status"] = "AT RISK"
    for c in state.get("carriers", []):
        c["reliability"] = max(50, int(c.get("reliability", 90)) - severity // 10)
    return state


def apply_disruption(state: dict, payload: dict) -> dict:
    dtype = payload.get("type", "late_pickup")
    handler = DISRUPTION_HANDLERS.get(dtype, late_pickup)
    return handler(state, payload)
