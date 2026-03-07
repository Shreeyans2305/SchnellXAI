from langchain_core.tools import tool


@tool
def run_what_if_simulation(shipment_id: str, scenarios: list[dict]) -> dict:
    """Run a quick what-if simulation comparing routing options."""
    scored = []
    for s in scenarios:
        cost_penalty = min(40, int(s.get("cost_delta_inr", 0)) // 200)
        net_score = max(0, 100 - cost_penalty - (int(s.get("eta_delta_minutes", 0)) // 10))
        scored.append({**s, "net_score": net_score, "blast_radius": 2, "recommended": False})
    if scored:
        best = max(scored, key=lambda x: x.get("net_score", 0))
        best["recommended"] = True
    return {"shipment_id": shipment_id, "options": scored}
