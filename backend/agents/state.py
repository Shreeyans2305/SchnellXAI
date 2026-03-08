from typing import TypedDict


class AgentState(TypedDict):
    shipments: list[dict]
    hubs: list[dict]
    carriers: list[dict]

    observations: list[dict]
    observer_summary: str

    hypotheses: list[dict]
    patterns_detected: list[str]
    reasoner_summary: str

    actions: list[dict]
    queued_approvals: list[dict]
    decider_summary: str

    executed_actions: list[dict]
    executor_summary: str

    lessons: list[dict]
    learner_summary: str

    cycle_id: str
    timestamp: str
    event_log: list[dict]

    # Batched pipeline fields
    buffered_anomalies: list[dict]   # raw disruptions collected since last cycle
    anomaly_history: list[dict]      # long-term anomaly log for learning context
