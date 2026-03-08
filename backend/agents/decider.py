import json
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from agents.state import AgentState
from config import settings
from db.store import get_db
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory

llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)

SYSTEM_PROMPT = f"""You are the Decider agent in a logistics AI system.
Given hypotheses and constraints, decide which actions to take.

Action types available:
  - reroute_shipment: reroute one shipment to an alternate path
  - temporary_hub_reroute: when a hub is congested/disrupted, reroute ALL traffic that
    passes through it to bypass hubs. List every affected shipment in
    affected_shipments and provide bypass_hubs.
  - notify_carrier: alert a carrier about a problem
  - reallocate_inventory: shift inventory between hubs
  - escalate_to_human: escalate for manual intervention

Autonomy rules — the system should be MOSTLY AUTONOMOUS:
  - autonomous=true for risk < {settings.human_approval_threshold} (most actions)
  - autonomous=false ONLY for risk >= {settings.human_approval_threshold} (critical, multi-hub cascading failures)
  - Individual shipment reroutes should almost always be autonomous
  - Carrier notifications and inventory moves are always autonomous
  - Only bulk hub reroutes affecting 4+ shipments with risk >= {settings.human_approval_threshold} need human approval

For hub_congestion hypotheses, PREFER a single temporary_hub_reroute action that covers
ALL shipments passing through the congested hub, rather than individual reroute_shipment
actions per shipment.

Output ONLY a JSON object with actions and queued_approvals."""


# Well-known bypass alternatives for major hubs
_HUB_BYPASSES: dict[str, list[str]] = {
    "nagpur": ["Pune Hub", "Bhopal Hub"],
    "mumbai": ["Pune Hub", "Ahmedabad Hub"],
    "delhi": ["Jaipur Hub", "Lucknow Hub"],
    "bangalore": ["Chennai Hub", "Hyderabad Hub"],
    "kolkata": ["Lucknow Hub", "Bhopal Hub"],
    "chennai": ["Bangalore Hub", "Hyderabad Hub"],
    "hyderabad": ["Bangalore Hub", "Chennai Hub"],
    "pune": ["Mumbai Hub", "Ahmedabad Hub"],
    "ahmedabad": ["Mumbai Hub", "Jaipur Hub"],
    "jaipur": ["Delhi Hub", "Ahmedabad Hub"],
    "lucknow": ["Delhi Hub", "Kolkata Hub"],
    "bhopal": ["Nagpur Hub", "Jaipur Hub"],
}


# Hub coordinates for distance-based routing
_HUB_COORDS: dict[str, tuple[float, float]] = {
    "mumbai": (19.076, 72.877),
    "delhi": (28.704, 77.102),
    "bangalore": (12.971, 77.594),
    "chennai": (13.082, 80.270),
    "kolkata": (22.572, 88.363),
    "hyderabad": (17.385, 78.486),
    "pune": (18.520, 73.856),
    "ahmedabad": (23.022, 72.571),
    "jaipur": (26.912, 75.787),
    "lucknow": (26.846, 80.946),
    "nagpur": (21.145, 79.088),
    "bhopal": (23.259, 77.412),
}


def _hub_key(name: str) -> str:
    """Normalise hub name for lookup: 'Nagpur Hub' → 'nagpur'."""
    return name.lower().replace(" hub", "").replace(" ", "")


def _hub_display(key: str) -> str:
    """Convert key back to display name: 'nagpur' → 'Nagpur Hub'."""
    return key.capitalize() + " Hub"


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Approx Euclidean distance (good enough for sorting Indian hubs)."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _nearest_hub(congested_key: str, exclude: set[str] | None = None) -> str:
    """Find the geographically nearest hub to the congested one."""
    exclude = exclude or set()
    exclude.add(congested_key)
    origin = _HUB_COORDS.get(congested_key)
    if not origin:
        bypass = _HUB_BYPASSES.get(congested_key, ["Nearest Hub"])
        return bypass[0]
    candidates = [
        (k, _distance(origin, coord))
        for k, coord in _HUB_COORDS.items()
        if k not in exclude
    ]
    candidates.sort(key=lambda x: x[1])
    return _hub_display(candidates[0][0]) if candidates else "Nearest Hub"


def _build_proposed_route(
    shipment: dict, congested_hub_key: str, bypass_hubs: list[str]
) -> list[str]:
    """Build a concrete proposed route for a shipment, replacing the congested hub
    with the nearest bypass hub while preserving origin and destination."""
    route_str = shipment.get("route", "")
    parts = []
    if "→" in route_str:
        parts = [p.strip() for p in route_str.split("→")]
    elif "->" in route_str:
        parts = [p.strip() for p in route_str.split("->")
        ]
    if len(parts) < 2:
        # Can't parse route — just use bypass hubs
        return bypass_hubs

    origin, destination = parts[0], parts[-1]
    # Pick the bypass hub that's closest to the destination
    dest_key = _hub_key(destination)
    dest_coord = _HUB_COORDS.get(dest_key)
    if dest_coord and bypass_hubs:
        scored = []
        for bh in bypass_hubs:
            bk = _hub_key(bh)
            bc = _HUB_COORDS.get(bk)
            if bc:
                scored.append((bh, _distance(bc, dest_coord)))
            else:
                scored.append((bh, 999))
        scored.sort(key=lambda x: x[1])
        best_bypass = scored[0][0]
    else:
        best_bypass = bypass_hubs[0] if bypass_hubs else _nearest_hub(congested_hub_key)

    return [origin, best_bypass, destination]


def _fallback_actions(hypotheses: list[dict], shipments: list[dict] | None = None) -> dict:
    shipments = shipments or []
    actions = []
    approvals = []
    handled_hubs: set[str] = set()

    # --- Pass 1: hub congestion → single bulk temporary_hub_reroute ----------
    for h in hypotheses:
        h_type = h.get("type", "")
        hub_name = h.get("hub", "")
        hub_norm = _hub_key(hub_name)
        if h_type not in ("hub_congestion", "late_pickup") or not hub_name or hub_norm in handled_hubs:
            continue

        # Find ALL shipments whose route passes through this hub
        affected_sids: list[str] = []
        for s in (h.get("affected_shipments") or []):
            if s and s != "?":
                affected_sids.append(s)
        for s in shipments:
            route_str = s.get("route", "")
            if hub_norm in _hub_key(route_str) and s.get("id") not in affected_sids:
                affected_sids.append(s["id"])
        if not affected_sids:
            continue

        handled_hubs.add(hub_norm)
        risk = int(100 * float(h.get("confidence", 0.75)))
        bypass_hubs = _HUB_BYPASSES.get(hub_norm, [_nearest_hub(hub_norm)])

        # Build per-shipment proposed routes
        ship_map = {s.get("id", ""): s for s in shipments}
        per_shipment_routes: dict[str, list[str]] = {}
        for sid in affected_sids:
            ship = ship_map.get(sid, {})
            per_shipment_routes[sid] = _build_proposed_route(ship, hub_norm, bypass_hubs)

        # Autonomy: only escalate to human when both risk is critical AND blast radius is large
        needs_approval = risk >= settings.human_approval_threshold and len(affected_sids) >= 4

        act = {
            "id": f"ACT-{str(uuid.uuid4())[:8].upper()}",
            "type": "temporary_hub_reroute",
            "target_hub": hub_name,
            "affected_shipments": affected_sids,
            "params": {
                "hub": hub_name,
                "bypass_hubs": bypass_hubs,
                "affected_shipments": affected_sids,
                "per_shipment_routes": per_shipment_routes,
                "eta_delta_minutes": 45 + len(affected_sids) * 15,
            },
            "autonomous": not needs_approval,
            "risk_score": risk,
            "rationale": (
                f"Major congestion detected at {hub_name}. "
                f"{len(affected_sids)} shipment(s) currently routed through this hub "
                f"should be temporarily rerouted via {', '.join(bypass_hubs)} "
                f"to avoid cascading delays."
            ),
        }
        actions.append(act)

    # --- Pass 2: remaining non-hub hypotheses → individual reroutes ----------
    for h in hypotheses:
        h_type = h.get("type", "")
        hub_norm = _hub_key(h.get("hub", ""))
        if h_type in ("hub_congestion", "late_pickup") and hub_norm in handled_hubs:
            continue  # already handled as bulk reroute
        sids = [s for s in (h.get("affected_shipments") or []) if s and s != "?"]
        if not sids:
            continue
        ship_map = {s.get("id", ""): s for s in shipments}
        hub_norm = _hub_key(h.get("hub", ""))
        bypass_hubs = _HUB_BYPASSES.get(hub_norm, [_nearest_hub(hub_norm)])
        for sid in sids:
            risk = int(100 * float(h.get("confidence", 0.6)))
            ship = ship_map.get(sid, {})
            proposed = _build_proposed_route(ship, hub_norm, bypass_hubs)
            act = {
                "id": f"ACT-{str(uuid.uuid4())[:8].upper()}",
                "type": "reroute_shipment",
                "target_shipment_id": sid,
                "params": {
                    "shipment_id": sid,
                    "new_route": proposed,
                    "carrier": h.get("carrier", "BlueDart"),
                    "eta_delta_minutes": 90,
                },
                "autonomous": risk < settings.human_approval_threshold,
                "risk_score": risk,
                "rationale": h.get("root_cause", "Risk analysis indicates rerouting is optimal."),
            }
            actions.append(act)

    return {"actions": actions, "queued_approvals": []}


def _normalize_approvals(
    actions: list[dict], raw_approvals: list, shipments: list[dict]
) -> list[dict]:
    """Ensure every non-autonomous action has a rich, complete approval entry."""
    ship_map = {s.get("id", ""): s for s in shipments}

    # Collect LLM-generated approvals keyed by shipment_id
    apr_by_ship: dict[str, dict] = {}
    for apr in raw_approvals:
        if not isinstance(apr, dict):
            continue
        sid = apr.get("shipment_id") or apr.get("target_shipment_id") or "?"
        apr_by_ship[sid] = apr

    normalized = []
    for act in actions:
        if not isinstance(act, dict):
            continue
        # Force non-autonomous when risk exceeds threshold
        risk = int(act.get("risk_score", 0))
        if risk >= settings.human_approval_threshold:
            act["autonomous"] = False
        if act.get("autonomous"):
            continue  # autonomous actions don't need approval

        sid = act.get("target_shipment_id") or act.get("shipment_id") or "?"
        existing = apr_by_ship.pop(sid, {})
        ship = ship_map.get(sid, {})

        # Derive current route from shipment data
        current_route = existing.get("current_route") or []
        if not current_route:
            route_str = ship.get("route", "")
            if route_str and "\u2192" in route_str:
                current_route = [r.strip() for r in route_str.split("\u2192")]
            elif route_str and "->" in route_str:
                current_route = [r.strip() for r in route_str.split("->")]

        proposed_route = (
            existing.get("proposed_route")
            or act.get("params", {}).get("new_route", [])
        )

        action_type = act.get("type", "reroute_shipment")

        # ── Hub-level bulk reroute ──────────────────────────────
        if action_type == "temporary_hub_reroute":
            target_hub = act.get("target_hub") or act.get("params", {}).get("hub", "")
            affected = act.get("affected_shipments") or act.get("params", {}).get("affected_shipments", [])
            # Ensure affected is a list of strings, not dicts
            affected = [
                (a if isinstance(a, str) else a.get("id", ""))
                for a in affected
                if a
            ]
            bypass = act.get("params", {}).get("bypass_hubs", [])
            per_routes = act.get("params", {}).get("per_shipment_routes", {})

            # --- Resolve vague hub name ("Hub") to actual congested hub ---
            hub_norm = _hub_key(target_hub)
            if not hub_norm or hub_norm == "hub":
                # Find first congested hub from live shipment data
                for s in shipments:
                    route_str = s.get("route", "")
                    for hk in _HUB_COORDS:
                        if hk in route_str.lower():
                            candidate = _hub_display(hk)
                            if _HUB_BYPASSES.get(hk):
                                target_hub = candidate
                                hub_norm = hk
                                break
                    if hub_norm and hub_norm != "hub":
                        break
                if not hub_norm or hub_norm == "hub":
                    # Last resort: pick first hub that has bypass info
                    for hk in _HUB_BYPASSES:
                        target_hub = _hub_display(hk)
                        hub_norm = hk
                        break

            # --- Always compute bypass hubs if missing ---
            if not bypass:
                bypass = _HUB_BYPASSES.get(hub_norm, [_nearest_hub(hub_norm)])

            # --- Find affected shipments from route data if list is empty ---
            if not affected and hub_norm:
                for s in shipments:
                    r = s.get("route", "").lower()
                    if hub_norm in r and s.get("id"):
                        affected.append(s["id"])

            # --- Always compute per-shipment routes if missing ---
            if not per_routes and affected:
                for a_sid in affected:
                    a_ship = ship_map.get(a_sid, {})
                    per_routes[a_sid] = _build_proposed_route(a_ship, hub_norm, bypass)

            # --- Build current routes from actual shipment data ---
            current_routes_by_ship: dict[str, list[str]] = {}
            for a_sid in affected:
                a_ship = ship_map.get(a_sid, {})
                r = a_ship.get("route", "")
                if "→" in r:
                    current_routes_by_ship[a_sid] = [p.strip() for p in r.split("→")]
                elif "->" in r:
                    current_routes_by_ship[a_sid] = [p.strip() for p in r.split("->")]

            blast = len(affected) if affected else 2

            apr = {
                "id": existing.get("id") or f"APR-{str(uuid.uuid4())[:8].upper()}",
                "shipment_id": target_hub,
                "action_type": action_type,
                "action": f"Temporarily reroute all traffic away from {target_hub}",
                "reason": (
                    existing.get("reason")
                    or act.get("rationale")
                    or f"Major congestion at {target_hub} — all inbound/outbound traffic should be rerouted."
                ),
                "target_hub": target_hub,
                "affected_shipments": affected,
                "bypass_hubs": bypass,
                "per_shipment_routes": per_routes,
                "current_routes_by_ship": current_routes_by_ship,
                "sla_impact": existing.get("sla_impact") or f"+{max(1, blast // 2)}h",
                "current_route": [target_hub],
                "proposed_route": bypass,
                "net_score": existing.get("net_score") or max(10, 100 - risk),
                "blast_radius": blast,
                "risk_score": risk or 80,
            }
            normalized.append(apr)
            continue

        # ── Individual shipment action ──────────────────────────
        action_labels = {
            "reroute_shipment": f"Reroute {sid} via alternate route",
            "notify_carrier": f"Notify carrier about {sid}",
            "reallocate_inventory": f"Reallocate inventory for {sid}",
            "escalate_to_human": f"Escalate {sid} to operations",
        }
        action_label = action_labels.get(action_type, f"Action required for {sid}")

        apr = {
            "id": existing.get("id") or f"APR-{str(uuid.uuid4())[:8].upper()}",
            "shipment_id": sid,
            "action_type": action_type,
            "action": existing.get("action") or action_label,
            "reason": (
                existing.get("reason")
                or act.get("rationale")
                or "Risk threshold exceeded \u2014 requires human authorization."
            ),
            "sla_impact": existing.get("sla_impact") or "+2h",
            "current_route": current_route,
            "proposed_route": proposed_route,
            "net_score": existing.get("net_score") or max(10, 100 - risk),
            "blast_radius": existing.get("blast_radius") or 2,
            "risk_score": risk,
        }
        normalized.append(apr)

    # Include remaining raw approvals that didn't match any action
    for sid, apr in apr_by_ship.items():
        apr.setdefault("id", f"APR-{str(uuid.uuid4())[:8].upper()}")
        apr.setdefault("shipment_id", sid)
        apr.setdefault("action", f"Requires approval for {sid}")
        apr.setdefault("action_type", "reroute_shipment")
        apr.setdefault("reason", "Risk analysis flagged this for human review.")
        apr.setdefault("sla_impact", "\u2014")
        apr.setdefault("current_route", [])
        apr.setdefault("proposed_route", [])
        apr.setdefault("net_score", 50)
        apr.setdefault("blast_radius", 1)
        normalized.append(apr)

    return normalized


def decider_node(state: AgentState) -> AgentState:
    hypotheses = state.get("hypotheses", [])

    # ── Pattern-strength guard: only act on moderate/strong patterns ──
    actionable = []
    for h in hypotheses:
        strength = h.get("pattern_strength", "").lower()
        evidence = int(h.get("evidence_count", 1))
        if strength in ("strong", "moderate") or evidence >= 2:
            actionable.append(h)
    hypotheses = actionable

    if not hypotheses:
        return {**state, "actions": [], "queued_approvals": [], "decider_summary": "No action needed."}

    user_msg = f"""
Hypotheses from Reasoner:
{json.dumps(hypotheses, indent=2)}

Current shipments:
{json.dumps(state['shipments'], indent=2)}

Decide on actions. Output JSON only.
"""

    try:
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```", maxsplit=2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        if not isinstance(result, dict):
            result = _fallback_actions(hypotheses, state.get("shipments", []))
    except Exception:
        result = _fallback_actions(hypotheses, state.get("shipments", []))

    actions = result.get("actions", [])
    actions = [a for a in actions if isinstance(a, dict)]  # guard bad LLM output
    raw_approvals = result.get("queued_approvals", [])
    approvals = _normalize_approvals(actions, raw_approvals, state.get("shipments", []))

    now = datetime.utcnow().isoformat()
    cycle_id = state.get("cycle_id", "?")
    with get_db() as conn:
        for apr in approvals:
            apr.setdefault("id", f"APR-{str(uuid.uuid4())[:8].upper()}")
            conn.execute(
                """
                INSERT OR REPLACE INTO approvals
                (id, shipment_id, action, details_json, status, created_at)
                VALUES (?,?,?,?,?,?)
            """,
                (
                    apr["id"],
                    apr.get("shipment_id", "?"),
                    apr.get("action", "?"),
                    json.dumps(apr),
                    "pending",
                    now,
                ),
            )
            short_term_memory.push(
                ShortTermEvent(
                    cycle_id=cycle_id,
                    timestamp=now,
                    event_type="APPROVAL",
                    flow="decider → human",
                    message=f"{apr.get('shipment_id', '?')} requires approval — {apr.get('action', '')}",
                    metadata=apr,
                )
            )

    for act in actions:
        if act.get("autonomous"):
            short_term_memory.push(
                ShortTermEvent(
                    cycle_id=cycle_id,
                    timestamp=now,
                    event_type="REROUTE" if act.get("type") == "reroute_shipment" else "EXECUTE",
                    flow="decider → executor",
                    message=f"{act.get('target_shipment_id', '?')} — {act.get('rationale', '')}",
                    metadata=act,
                )
            )

    return {
        **state,
        "actions": actions,
        "queued_approvals": approvals,
        "decider_summary": f"{len(actions)} actions decided, {len(approvals)} pending approval.",
    }
