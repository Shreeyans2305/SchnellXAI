from fastapi import APIRouter

from data.seed import get_live_state

router = APIRouter()


def _hub_lookup(hubs: list[dict]) -> dict[str, dict]:
    out = {}
    for h in hubs:
        name = str(h.get("name", "")).replace(" Hub", "").strip()
        out[name] = h
    return out


@router.get("/shipments")
def get_shipments():
    state = get_live_state()
    return state.get("shipments", [])


@router.get("/shipments/locations")
def get_shipment_locations():
    state = get_live_state()
    shipments = state.get("shipments", [])
    hubs = state.get("hubs", state.get("warehouses", []))
    by_name = _hub_lookup(hubs)

    markers = []
    for s in shipments:
        route = str(s.get("route", "Mumbai → Delhi")).split(" → ")
        frm_name = route[0].strip() if route else "Mumbai"
        to_name = route[1].strip() if len(route) > 1 else "Delhi"
        frm = by_name.get(frm_name, {"lat": 19.076, "lng": 72.877})
        to = by_name.get(to_name, {"lat": 28.704, "lng": 77.102})
        ratio = max(0.0, min(1.0, float(s.get("progress", 0)) / 100.0))
        lat = float(frm["lat"]) + (float(to["lat"]) - float(frm["lat"])) * ratio
        lng = float(frm["lng"]) + (float(to["lng"]) - float(frm["lng"])) * ratio
        markers.append(
            {
                "id": s.get("id"),
                "lat": round(lat, 4),
                "lng": round(lng, 4),
                "from": {"lat": float(frm["lat"]), "lng": float(frm["lng"])} ,
                "to": {"lat": float(to["lat"]), "lng": float(to["lng"])} ,
                "status": s.get("status", "ON TRACK"),
            }
        )

    return markers
