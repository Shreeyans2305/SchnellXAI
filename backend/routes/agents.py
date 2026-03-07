from fastapi import APIRouter

from memory.short_term import short_term_memory

router = APIRouter()

AGENT_COLORS = {
    "observer": "#3b82f6",
    "reasoner": "#8b5cf6",
    "decider": "#f5a623",
    "executor": "#42d65c",
    "learner": "#b32826",
}


@router.get("/agents/status")
def agents_status():
    recent = short_term_memory.recent(50)
    agent_stats = {name: {"messages": 0, "last_action": ""} for name in AGENT_COLORS}
    for e in recent:
        src = e.flow.split(" → ")[0].strip().lower()
        if src in agent_stats:
            agent_stats[src]["messages"] += 1
            if not agent_stats[src]["last_action"]:
                agent_stats[src]["last_action"] = e.message

    agents = [
        {
            "id": k,
            "name": k.capitalize(),
            "status": "active",
            "load": min(100, agent_stats[k]["messages"] * 4 + 10),
            "messagesProcessed": agent_stats[k]["messages"],
            "lastAction": agent_stats[k]["last_action"] or "Idle",
            "color": AGENT_COLORS[k],
        }
        for k in AGENT_COLORS
    ]

    edges = [
        {"from": "observer", "to": "reasoner", "active": True},
        {"from": "reasoner", "to": "decider", "active": True},
        {"from": "decider", "to": "executor", "active": True},
        {"from": "executor", "to": "learner", "active": True},
        {"from": "learner", "to": "observer", "active": True},
    ]
    return {"agents": agents, "edges": edges}


@router.get("/agent/events")
def agent_events():
    recent = short_term_memory.recent(30)
    return [
        {
            "id": i + 1,
            "time": e.timestamp[11:19],
            "type": e.event_type,
            "flow": e.flow,
            "message": e.message,
        }
        for i, e in enumerate(recent)
    ]
