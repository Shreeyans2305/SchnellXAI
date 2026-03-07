from dataclasses import dataclass, field


@dataclass
class ShortTermEvent:
    cycle_id: str
    timestamp: str
    event_type: str
    flow: str
    message: str
    metadata: dict = field(default_factory=dict)


@dataclass
class LongTermEpisode:
    episode_id: str
    timestamp: str
    pattern_signature: str
    context: dict
    action_taken: str
    outcome: str
    confidence_delta: float


@dataclass
class PatternRecord:
    signature: str
    description: str
    occurrences: int
    last_seen: str
    avg_confidence: float
    recommended_action: str
