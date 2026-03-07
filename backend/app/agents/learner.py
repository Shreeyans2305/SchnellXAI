from __future__ import annotations

from statistics import mean
from typing import Dict

from .base import AgentOutput
from ..learning import ReplayEntry, get_replay_buffer
from ..models.domain import AgentEvent, EventType
from ..state import GlobalState


async def run_learner(state: GlobalState) -> AgentOutput:
    """
    Learner: evaluate past decisions and adjust simple parameters.

    For demonstration, we:
    - Track whether recent actions reduced the combined atRisk+delayed metric.
    - Emit LEARNING events summarizing success rates.
    - Slightly adjust carrier reliability scores as a proxy for learned priors.
    """
    output = AgentOutput()
    buffer = get_replay_buffer()

    # Translate decision log entries into replay entries and clear the log
    for action_id, description, metric_span in state.decision_log:
        try:
            before_str, after_str = metric_span.split("->")
            before_metric = int(before_str)
            after_metric = int(after_str)
        except ValueError:
            continue
        buffer.add(
            ReplayEntry(
                action_id=action_id,
                description=description,
                before_metric=before_metric,
                after_metric=after_metric,
            )
        )
    state.decision_log.clear()

    entries = buffer.last_n(50)
    if not entries:
        return output

    deltas = [e.before_metric - e.after_metric for e in entries]
    success_rate = sum(1 for d in deltas if d > 0) / len(deltas)
    avg_delta = mean(deltas)

    # Adjust carrier reliability very slightly based on average improvement.
    # This is intentionally simple and interpretable.
    adjustment = 1 if avg_delta > 0 else -1
    for carrier in state.carriers.values():
        carrier.reliability = max(70, min(99, carrier.reliability + adjustment))

    summary = (
        f"Learner evaluated {len(entries)} past decisions: "
        f"success_rate={success_rate:.2f}, avg_metric_delta={avg_delta:.2f}. "
        f"Carrier reliability adjusted by {adjustment}."
    )
    output.explanation = summary

    ev = AgentEvent(
        id=len(state.events) + 1,
        time="",
        type=EventType.LEARNING,
        flow="learner \u2192 all",
        message=summary,
    )
    state.enqueue_event(ev)

    return output

