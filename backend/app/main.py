from contextlib import asynccontextmanager

import asyncio
from fastapi import FastAPI

from .api import router as api_router
from .config import settings
from .data import seed_state
from .state import get_state


async def _start_background_tasks() -> None:
    """
    Start simulation and agent orchestration background tasks.

    The concrete implementations are provided by the orchestrator module;
    imports are done lazily to avoid circular dependencies.
    """
    from .agents.orchestrator import (
        run_agent_cycle_forever,
        run_simulation_loop_forever,
    )

    state = get_state()
    loop = asyncio.get_event_loop()

    state.simulation_task = loop.create_task(run_simulation_loop_forever(state))
    state.agent_cycle_task = loop.create_task(run_agent_cycle_forever(state))


async def _stop_background_tasks() -> None:
    state = get_state()
    for task in (state.simulation_task, state.agent_cycle_task):
        if task is not None and not task.done():
            task.cancel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup/shutdown hooks."""
    # Initialize in-memory state and seed with demo data
    state = get_state()
    seed_state(state)

    # Start simulation and agent background loops
    await _start_background_tasks()
    try:
        yield
    finally:
        await _stop_background_tasks()


app = FastAPI(
    title="SchnellXAI Logistics Agent Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_prefix)

