from fastapi import APIRouter

from data.seed import get_live_state

router = APIRouter()


@router.get("/hubs")
def get_hubs():
    state = get_live_state()
    return state.get("hubs", state.get("warehouses", []))
