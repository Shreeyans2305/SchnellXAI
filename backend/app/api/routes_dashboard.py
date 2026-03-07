from fastapi import APIRouter

from ..state import get_state
from ..models.domain import AgentEvent, DashboardMetrics


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """
    Return the latest dashboard metrics derived from global state.
    """
    state = get_state()
    # Metrics are periodically recomputed by the orchestrator; fall back to a
    # simple default if they are not yet initialized.
    if state.metrics is None:
        from ..agents.orchestrator import _recompute_metrics  # type: ignore[attr-defined]

        _recompute_metrics(state)
    return state.metrics


@router.get("/agent/events", response_model=list[AgentEvent])
async def get_agent_events():
    """
    Return recent multi-agent events for the EventTicker.
    """
    state = get_state()
    return list(state.events)

