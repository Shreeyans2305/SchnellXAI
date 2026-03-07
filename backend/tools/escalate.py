from datetime import datetime

from langchain_core.tools import tool

from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory


@tool
def escalate_to_human(shipment_id: str, reason: str, urgency: str) -> dict:
    """Escalate a shipment decision to a human operator."""
    short_term_memory.push(
        ShortTermEvent(
            cycle_id="exec",
            timestamp=datetime.utcnow().isoformat(),
            event_type="ALERT",
            flow="executor → human",
            message=f"ESCALATION [{urgency}] {shipment_id}: {reason}",
        )
    )
    return {"escalated": True, "shipment_id": shipment_id, "urgency": urgency}
