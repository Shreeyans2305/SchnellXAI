"""
Anomaly buffer — collects disruption events and raw anomalies over a time window
so the pipeline can process them in batches instead of one-at-a-time.
"""

import json
import uuid
from collections import deque
from datetime import datetime
from threading import Lock

from db.store import get_db


class AnomalyBuffer:
    """Thread-safe buffer that collects anomalies between pipeline cycles."""

    def __init__(self):
        self._buffer: deque[dict] = deque(maxlen=200)
        self._lock = Lock()

    # ── Write ────────────────────────────────────────────

    def push(self, anomaly: dict):
        """Add a single anomaly event to the buffer."""
        anomaly.setdefault("buffered_at", datetime.utcnow().isoformat())
        anomaly.setdefault("id", f"ANM-{str(uuid.uuid4())[:8].upper()}")
        with self._lock:
            self._buffer.append(anomaly)
        # Also persist to long-term anomaly log so the learner can reference history
        self._persist(anomaly)

    # ── Read / Drain ─────────────────────────────────────

    def drain(self) -> list[dict]:
        """Pop all buffered anomalies (atomic). Returns list, empties the buffer."""
        with self._lock:
            items = list(self._buffer)
            self._buffer.clear()
        return items

    def peek(self) -> list[dict]:
        """Non-destructive read of current buffer contents."""
        with self._lock:
            return list(self._buffer)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._buffer)

    # ── Long-term anomaly log ────────────────────────────

    @staticmethod
    def _persist(anomaly: dict):
        """Write the raw anomaly to the anomaly_log table for long-term learning."""
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO anomaly_log
                       (id, timestamp, type, source, severity, target_shipment, target_hub, payload_json)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        anomaly.get("id", str(uuid.uuid4())[:8]),
                        anomaly.get("buffered_at", datetime.utcnow().isoformat()),
                        anomaly.get("type", "unknown"),
                        anomaly.get("source", "disruption"),
                        int(anomaly.get("severity", 50)),
                        anomaly.get("targetShipmentId", ""),
                        str(anomaly.get("targetWarehouseId", "")),
                        json.dumps(anomaly),
                    ),
                )
        except Exception:
            pass  # non-critical — don't crash the buffer

    @staticmethod
    def recent_history(n: int = 50) -> list[dict]:
        """Fetch the last N logged anomalies from long-term storage (for the learner)."""
        try:
            with get_db() as conn:
                rows = conn.execute(
                    "SELECT * FROM anomaly_log ORDER BY timestamp DESC LIMIT ?", (n,)
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


anomaly_buffer = AnomalyBuffer()
