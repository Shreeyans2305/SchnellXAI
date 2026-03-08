"""Injects realistic disruptions into a scenario state."""

import random

DISRUPTION_HANDLERS = {}


def disruption(name):
    def decorator(fn):
        DISRUPTION_HANDLERS[name] = fn
        return fn

    return decorator


# ── Late Pickup ──────────────────────────────────────────
@disruption("late_pickup")
def late_pickup(state: dict, payload: dict) -> dict:
    target = payload.get("targetShipmentId")
    severity = int(payload.get("severity", 60))
    delay_minutes = int(payload.get("delayMinutes", 90))
    reason = payload.get("reason", "Carrier failed to collect on time")
    for s in state.get("shipments", []):
        if s.get("id") == target or (target is None and s.get("status") != "DELAYED"):
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 2)
            s["status"] = "DELAYED"
            s["etaMinutes"] = int(s.get("etaMinutes", 200)) + delay_minutes
            s["notes"] = f"Late pickup — {reason} (+{delay_minutes}m delay, severity {severity})"
            if target:
                break  # only affect the targeted shipment
    return state


# ── Warehouse / Hub Congestion ───────────────────────────
@disruption("warehouse_congestion")
def warehouse_congestion(state: dict, payload: dict) -> dict:
    hub_id = payload.get("targetWarehouseId") or payload.get("targetHubId")
    severity = int(payload.get("severity", 60))
    congestion_pct = int(payload.get("congestionPercent", 80))
    hubs = state.get("hubs") or state.get("warehouses", [])
    hub_name = "Unknown Hub"
    hub_short = ""
    for h in hubs:
        if str(h.get("id")) == str(hub_id):
            h["status"] = "congested"
            h["shipments"] = min(int(h.get("shipments", 120)) + random.randint(40, 120), 600)
            hub_name = h.get("name", hub_name)
            hub_short = hub_name.replace(" Hub", "").strip().lower()
    # Only raise risk on shipments whose route passes through the congested hub
    risk_bump = max(10, severity // 3)
    for s in state.get("shipments", []):
        route_lower = s.get("route", "").lower()
        if hub_short and hub_short not in route_lower:
            continue  # shipment doesn't route through this hub — leave it alone
        s["risk"] = min(100, int(s.get("risk", 30)) + risk_bump)
        if s["risk"] >= 80:
            s["status"] = "DELAYED"
            s["notes"] = f"Warehouse congestion at {hub_name} — throughput at {congestion_pct}% capacity"
        elif s["risk"] >= 55:
            s["status"] = "AT RISK"
            s["notes"] = f"Congestion warning — {hub_name} at {congestion_pct}% capacity"
    return state

# Keep old name as alias so both work
DISRUPTION_HANDLERS["hub_congestion"] = warehouse_congestion


# ── Inaccurate ETA ───────────────────────────────────────
@disruption("inaccurate_eta")
def inaccurate_eta(state: dict, payload: dict) -> dict:
    target = payload.get("targetShipmentId")
    severity = int(payload.get("severity", 60))
    drift_minutes = int(payload.get("driftMinutes", 120))
    drift_direction = payload.get("driftDirection", "later")  # 'later' or 'earlier'
    for s in state.get("shipments", []):
        if s.get("id") == target or (target is None and s.get("status") != "DELAYED"):
            delta = drift_minutes if drift_direction == "later" else -drift_minutes
            s["etaMinutes"] = max(0, int(s.get("etaMinutes", 200)) + delta)
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 3)
            direction_label = f"+{drift_minutes}m later" if drift_direction == "later" else f"-{drift_minutes}m earlier"
            s["notes"] = f"ETA recalculated — actual arrival {direction_label} than predicted (severity {severity})"
            if s["risk"] >= 80:
                s["status"] = "DELAYED"
            elif s["risk"] >= 55:
                s["status"] = "AT RISK"
            if target:
                break
    return state


# ── Cascading Reroute ────────────────────────────────────
@disruption("cascading_reroute")
def cascading_reroute(state: dict, payload: dict) -> dict:
    trigger_shipment = payload.get("targetShipmentId")
    hub_id = payload.get("targetWarehouseId") or payload.get("targetHubId")
    severity = int(payload.get("severity", 70))
    affected_count = int(payload.get("affectedCount", 3))

    hubs = state.get("hubs") or state.get("warehouses", [])
    hub_name = "Hub"
    for h in hubs:
        if str(h.get("id")) == str(hub_id):
            h["status"] = "congested"
            hub_name = h.get("name", hub_name)

    shipments = state.get("shipments", [])
    # Primary shipment gets major hit
    affected = 0
    for s in shipments:
        if s.get("id") == trigger_shipment:
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 2)
            s["status"] = "DELAYED"
            s["notes"] = f"Cascading reroute triggered — primary shipment blocked at {hub_name}"
            affected += 1
            break

    # Cascade: other shipments get secondary impact
    for s in shipments:
        if s.get("id") == trigger_shipment:
            continue
        if affected >= affected_count:
            break
        cascade_risk = max(10, severity // 4)
        s["risk"] = min(100, int(s.get("risk", 30)) + cascade_risk)
        if s["risk"] >= 80:
            s["status"] = "DELAYED"
        elif s["risk"] >= 55:
            s["status"] = "AT RISK"
        s["notes"] = f"Cascade impact — reroute ripple from {hub_name} (secondary)"
        affected += 1

    return state


# ── Carrier Degradation (bonus / legacy) ─────────────────
@disruption("carrier_degradation")
def carrier_degradation(state: dict, payload: dict) -> dict:
    target = payload.get("targetShipmentId")
    severity = int(payload.get("severity", 50))
    for s in state.get("shipments", []):
        if s.get("id") == target or target is None:
            s["risk"] = min(100, int(s.get("risk", 30)) + severity // 3)
            if s["risk"] >= 80:
                s["status"] = "DELAYED"
            elif s["risk"] >= 55:
                s["status"] = "AT RISK"
            s["notes"] = f"Carrier performance degradation — reliability dropping (severity {severity})"
    for c in state.get("carriers", []):
        c["reliability"] = max(50, int(c.get("reliability", 90)) - severity // 10)
    return state


def apply_disruption(state: dict, payload: dict) -> dict:
    dtype = payload.get("type", "late_pickup")
    handler = DISRUPTION_HANDLERS.get(dtype)
    if handler is None:
        raise ValueError(f"Unknown disruption type: {dtype}. Available: {list(DISRUPTION_HANDLERS.keys())}")
    return handler(state, payload)
