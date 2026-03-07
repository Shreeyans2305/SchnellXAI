from langchain_core.tools import tool


@tool
def reallocate_inventory(hub_id: str, sku: str, quantity: int, destination_hub_id: str) -> dict:
    """Reallocate inventory between hubs."""
    return {
        "reallocated": True,
        "hub_id": hub_id,
        "destination": destination_hub_id,
        "sku": sku,
        "quantity": quantity,
    }
