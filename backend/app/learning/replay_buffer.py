from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ReplayEntry:
    action_id: str
    description: str
    before_metric: int  # combined atRisk + delayed
    after_metric: int


class ReplayBuffer:
    """
    Simple in-memory + JSON-backed replay buffer for learner agent.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(__file__).with_suffix(".json")
        self.entries: List[ReplayEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
            self.entries = [
                ReplayEntry(
                    action_id=e["action_id"],
                    description=e["description"],
                    before_metric=e["before_metric"],
                    after_metric=e["after_metric"],
                )
                for e in data
            ]
        except Exception:  # noqa: BLE001
            self.entries = []

    def _save(self) -> None:
        try:
            payload = [asdict(e) for e in self.entries]
            self.path.write_text(json.dumps(payload, indent=2))
        except Exception:  # noqa: BLE001
            # Persistence failures should not break the main loop.
            pass

    def add(self, entry: ReplayEntry) -> None:
        self.entries.append(entry)
        # Keep buffer at a reasonable size
        if len(self.entries) > 500:
            self.entries = self.entries[-500:]
        self._save()

    def last_n(self, n: int = 50) -> List[ReplayEntry]:
        return self.entries[-n:]


_buffer: Optional[ReplayBuffer] = None


def get_replay_buffer() -> ReplayBuffer:
    global _buffer
    if _buffer is None:
        _buffer = ReplayBuffer()
    return _buffer

