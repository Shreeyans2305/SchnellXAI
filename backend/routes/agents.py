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

# Canonical agent-to-agent edges in the LangGraph pipeline
_ALL_EDGES = [
    ("observer", "reasoner"),
    ("reasoner", "decider"),
    ("decider", "executor"),
    ("decider", "human"),
    ("executor", "learner"),
    ("learner", "observer"),
    ("learner", "reasoner"),
]

# Map STM flow strings (src → dst) to normalised agent names
def _normalise_agent(name: str) -> str:
    n = name.strip().lower()
    if n in AGENT_COLORS or n == "human":
        return n
    # "system", "carrier", "all" etc → map back
    mapping = {"system": "executor", "carrier": "executor", "all": "learner"}
    return mapping.get(n, "")


@router.get("/agents/status")
def agents_status():
    recent = short_term_memory.recent(80)
    agent_stats = {
        name: {"messages": 0, "last_action": "", "last_event_type": ""}
        for name in AGENT_COLORS
    }
    active_flows: dict[tuple[str, str], int] = {}  # (src, dst) → count in recent window
    current_agent = ""  # the agent that most recently produced an event

    for e in recent:
        parts = e.flow.split("→")
        src_raw = parts[0].strip().lower() if len(parts) >= 1 else ""
        dst_raw = parts[1].strip().lower() if len(parts) >= 2 else ""
        src = _normalise_agent(src_raw)
        dst = _normalise_agent(dst_raw)

        if src in agent_stats:
            agent_stats[src]["messages"] += 1
            if not agent_stats[src]["last_action"]:
                agent_stats[src]["last_action"] = e.message
                agent_stats[src]["last_event_type"] = e.event_type

        if src and dst:
            key = (src, dst)
            active_flows[key] = active_flows.get(key, 0) + 1

        if not current_agent and src in AGENT_COLORS:
            current_agent = src

    agents = [
        {
            "id": k,
            "name": k.capitalize(),
            "status": "active" if agent_stats[k]["messages"] > 0 else "idle",
            "load": min(100, agent_stats[k]["messages"] * 4 + 10),
            "messagesProcessed": agent_stats[k]["messages"],
            "lastAction": agent_stats[k]["last_action"] or "Idle",
            "lastEventType": agent_stats[k]["last_event_type"] or "",
            "color": AGENT_COLORS[k],
        }
        for k in AGENT_COLORS
    ]

    # Build edges with real activity counts
    edges = []
    for src, dst in _ALL_EDGES:
        count = active_flows.get((src, dst), 0)
        edges.append(
            {
                "from": src,
                "to": dst,
                "active": count > 0,
                "messageCount": count,
            }
        )

    return {
        "agents": agents,
        "edges": edges,
        "currentAgent": current_agent or "observer",
    }


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
