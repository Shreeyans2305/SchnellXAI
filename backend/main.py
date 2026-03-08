from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.store import init_db
from pipeline.scheduler import pipeline_scheduler
from routes import agents, approvals, carriers, dashboard, hubs, shipments, simulation

app = FastAPI(title="Logistics Agent Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    import asyncio
    loop = asyncio.get_event_loop()
    pipeline_scheduler.start(loop)


@app.on_event("shutdown")
async def shutdown():
    pipeline_scheduler.stop()


app.include_router(agents.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(shipments.router, prefix="/api")
app.include_router(carriers.router, prefix="/api")
app.include_router(hubs.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
