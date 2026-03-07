from fastapi import APIRouter

from ..models.domain import Carrier, Hub, Shipment, ShipmentLocation
from ..state import get_state


router = APIRouter(tags=["shipments"])


@router.get("/shipments", response_model=list[Shipment])
async def list_shipments():
    state = get_state()
    return list(state.shipments.values())


@router.get("/carriers", response_model=list[Carrier])
async def list_carriers():
    state = get_state()
    return list(state.carriers.values())


@router.get("/hubs", response_model=list[Hub])
async def list_hubs():
    state = get_state()
    return list(state.hubs.values())


@router.get("/shipments/locations", response_model=list[ShipmentLocation])
async def list_shipment_locations():
    state = get_state()
    return list(state.shipment_locations.values())

