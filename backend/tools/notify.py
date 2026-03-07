from datetime import datetime

from langchain_core.tools import tool

from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory


@tool
def notify_carrier(carrier: str, shipment_id: str, message: str) -> dict:
    """Send an operational instruction to a carrier."""
    short_term_memory.push(
        ShortTermEvent(
            cycle_id="exec",
            timestamp=datetime.utcnow().isoformat(),
            event_type="EXECUTE",
            flow="executor → carrier",
            message=f"Carrier '{carrier}' notified for {shipment_id}: {message}",
        )
    )
    return {"notified": True, "carrier": carrier, "shipment_id": shipment_id}
