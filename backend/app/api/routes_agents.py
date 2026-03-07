from fastapi import APIRouter

from ..models.domain import Agent, AgentEdge
from ..state import get_state


router = APIRouter(tags=["agents"])


@router.get("/agents/status")
async def get_agents_status():
  """
  Return the current agent mesh: nodes and edges.
  """
  state = get_state()
  agents = [a for a in state.agents.values()]
  edges = [e.model_dump(by_alias=True) for e in state.agent_edges]
  return {"agents": agents, "edges": edges}

