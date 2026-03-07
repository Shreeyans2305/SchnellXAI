from datetime import datetime

from langchain_core.tools import tool

from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory


@tool
def reroute_shipment(shipment_id: str, new_route: list[str], carrier: str, eta_delta_minutes: int) -> dict:
    """Reroute a shipment to a new sequence of hubs via a specified carrier."""
    short_term_memory.push(
        ShortTermEvent(
            cycle_id="exec",
            timestamp=datetime.utcnow().isoformat(),
            event_type="EXECUTE",
            flow="executor → carrier",
            message=f"{shipment_id} rerouted via {' → '.join(new_route)} ({carrier}) ETA {eta_delta_minutes:+d}m",
        )
    )
    return {
        "success": True,
        "shipment_id": shipment_id,
        "new_route": new_route,
        "carrier": carrier,
        "eta_delta_minutes": eta_delta_minutes,
    }
