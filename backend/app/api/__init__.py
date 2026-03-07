from fastapi import APIRouter

from . import routes_agents, routes_approvals, routes_dashboard, routes_shipments, routes_simulation


router = APIRouter()

router.include_router(routes_dashboard.router)
router.include_router(routes_agents.router)
router.include_router(routes_shipments.router)
router.include_router(routes_approvals.router)
router.include_router(routes_simulation.router)

