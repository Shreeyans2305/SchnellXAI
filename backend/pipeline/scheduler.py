"""
Pipeline scheduler — runs the LangGraph agent pipeline on a fixed interval
(every ~25 seconds), draining the anomaly buffer each cycle so the agents
reason over batched events instead of reacting one-at-a-time.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from threading import Lock

from agents.graph import logistics_graph
from config import settings
from data.seed import get_live_state
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory
from pipeline.buffer import anomaly_buffer

logger = logging.getLogger("pipeline.scheduler")

CYCLE_INTERVAL_SECONDS = 25  # how often the pipeline runs


class PipelineScheduler:
    """Singleton background scheduler for the agentic pipeline."""

    def __init__(self):
        self._lock = Lock()
        self._running = False
        self._task: asyncio.Task | None = None

        # Latest cycle result (exposed to API)
        self.last_cycle: dict | None = None
        self.last_cycle_at: str | None = None
        self.cycles_completed: int = 0
        self.next_run_at: str | None = None

    # ── Lifecycle ────────────────────────────────────────

    def start(self, loop: asyncio.AbstractEventLoop | None = None):
        if self._running:
            return
        self._running = True
        if loop:
            self._task = loop.create_task(self._loop())
        else:
            self._task = asyncio.ensure_future(self._loop())
        logger.info("Pipeline scheduler started (every %ds)", CYCLE_INTERVAL_SECONDS)

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Pipeline scheduler stopped")

    # ── Main loop ────────────────────────────────────────

    async def _loop(self):
        while self._running:
            self.next_run_at = datetime.utcnow().isoformat()
            try:
                await self._run_cycle()
            except Exception as exc:
                logger.exception("Pipeline cycle failed: %s", exc)
            await asyncio.sleep(CYCLE_INTERVAL_SECONDS)

    async def _run_cycle(self):
        # 1) Drain buffered anomalies
        buffered = anomaly_buffer.drain()

        # 2) Get current logistics state
        state = get_live_state()
        shipments = state.get("shipments", [])
        hubs = state.get("hubs", state.get("warehouses", []))

        if not shipments:
            # No scenario loaded — nothing to do
            return

        # 3) Build cycle state with buffered anomalies injected
        cycle_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()

        # Push a cycle-start event
        short_term_memory.push(
            ShortTermEvent(
                cycle_id=cycle_id,
                timestamp=now,
                event_type="CYCLE",
                flow="scheduler → observer",
                message=f"Pipeline cycle {cycle_id} started — {len(buffered)} buffered anomalies",
                metadata={"buffered_count": len(buffered)},
            )
        )

        # Fetch recent anomaly history from the long-term log for context
        history = anomaly_buffer.recent_history(30)

        cycle_state = {
            "shipments": shipments,
            "hubs": hubs,
            "carriers": state.get("carriers", []),
            "observations": [],
            "hypotheses": [],
            "patterns_detected": [],
            "actions": [],
            "queued_approvals": [],
            "executed_actions": [],
            "lessons": [],
            "event_log": [],
            "observer_summary": "",
            "reasoner_summary": "",
            "decider_summary": "",
            "executor_summary": "",
            "learner_summary": "",
            "cycle_id": cycle_id,
            "timestamp": now,
            # ── New fields for batched processing ──
            "buffered_anomalies": buffered,
            "anomaly_history": history,
        }

        # 4) Run the full LangGraph pipeline
        result = await logistics_graph.ainvoke(cycle_state)

        # 5) Store the cycle result
        with self._lock:
            self.last_cycle = {
                "cycle_id": cycle_id,
                "timestamp": now,
                "buffered_anomalies_count": len(buffered),
                "observations": result.get("observations", []),
                "hypotheses": result.get("hypotheses", []),
                "actions": result.get("actions", []),
                "queued_approvals": len(result.get("queued_approvals", [])),
                "executed_actions": result.get("executed_actions", []),
                "lessons": result.get("lessons", []),
                "summaries": {
                    "observer": result.get("observer_summary", ""),
                    "reasoner": result.get("reasoner_summary", ""),
                    "decider": result.get("decider_summary", ""),
                    "executor": result.get("executor_summary", ""),
                    "learner": result.get("learner_summary", ""),
                },
            }
            self.last_cycle_at = now
            self.cycles_completed += 1

        logger.info(
            "Cycle %s complete: %d anomalies → %d observations → %d actions (%d approvals)",
            cycle_id,
            len(buffered),
            len(result.get("observations", [])),
            len(result.get("actions", [])),
            len(result.get("queued_approvals", [])),
        )

    # ── Status (for API) ────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "cycles_completed": self.cycles_completed,
                "interval_seconds": CYCLE_INTERVAL_SECONDS,
                "last_cycle_at": self.last_cycle_at,
                "next_run_in_seconds": CYCLE_INTERVAL_SECONDS,
                "buffered_anomalies": anomaly_buffer.count,
                "last_cycle": self.last_cycle,
            }


pipeline_scheduler = PipelineScheduler()
