from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

from ..config import settings
from ..models.domain import (
    Agent,
    AgentEdge,
    AgentEvent,
    Approval,
    CascadeImpact,
    Carrier,
    DashboardMetrics,
    Hub,
    Shipment,
    ShipmentLocation,
)


@dataclass
class GlobalState:
    """In-memory world state for the logistics simulation."""

    shipments: Dict[str, Shipment] = field(default_factory=dict)
    carriers: Dict[int, Carrier] = field(default_factory=dict)
    hubs: Dict[int, Hub] = field(default_factory=dict)
    logistics_routes: Dict[str, dict] = field(default_factory=dict)
    shipment_locations: Dict[str, ShipmentLocation] = field(default_factory=dict)

    agents: Dict[str, Agent] = field(default_factory=dict)
    agent_edges: List[AgentEdge] = field(default_factory=list)

    events: Deque[AgentEvent] = field(
        default_factory=lambda: deque(maxlen=settings.max_events)
    )
    approvals_queue: Deque[Approval] = field(default_factory=deque)

    metrics: Optional[DashboardMetrics] = None

    # (state_snapshot, action_description, outcome_summary)
    decision_log: List[Tuple[str, str, str]] = field(default_factory=list)

    # Background tasks references so we can cancel on shutdown if needed
    simulation_task: Optional[asyncio.Task] = None
    agent_cycle_task: Optional[asyncio.Task] = None

    def enqueue_event(self, event: AgentEvent) -> None:
        self.events.append(event)

    def enqueue_approval(self, approval: Approval) -> None:
        self.approvals_queue.append(approval)

    def pop_next_approval(self) -> Optional[Approval]:
        if self.approvals_queue:
            return self.approvals_queue[0]
        return None

    def remove_approval(self, approval_id: str) -> Optional[Approval]:
        """Remove an approval by id from the queue."""
        if not self.approvals_queue:
            return None

        buffer: list[Approval] = list(self.approvals_queue)
        removed: Optional[Approval] = None
        for idx, approval in enumerate(buffer):
            if approval.id == approval_id:
                removed = approval
                del buffer[idx]
                break

        if removed is not None:
            self.approvals_queue.clear()
            self.approvals_queue.extend(buffer)

        return removed


_state: Optional[GlobalState] = None


def get_state() -> GlobalState:
    global _state
    if _state is None:
        _state = GlobalState()
    return _state

