from collections import deque

from config import settings
from memory.schemas import ShortTermEvent


class ShortTermMemory:
    """Thread-safe enough for single-process FastAPI; keeps recent agent events."""

    def __init__(self):
        self._buffer: deque[ShortTermEvent] = deque(maxlen=settings.short_term_window)

    def push(self, event: ShortTermEvent):
        self._buffer.appendleft(event)

    def recent(self, n: int = 10) -> list[ShortTermEvent]:
        return list(self._buffer)[:n]

    def events_for_cycle(self, cycle_id: str) -> list[ShortTermEvent]:
        return [e for e in self._buffer if e.cycle_id == cycle_id]

    def to_context_string(self, n: int = 15) -> str:
        events = self.recent(n)
        if not events:
            return "No recent events."
        lines = [f"[{e.timestamp}] {e.event_type} ({e.flow}): {e.message}" for e in events]
        return "\n".join(lines)


short_term_memory = ShortTermMemory()
