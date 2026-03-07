import hashlib
import json
from datetime import datetime

from db.store import get_db
from memory.schemas import LongTermEpisode, PatternRecord


def _sig(anomaly_type: str, hub: str, carrier: str) -> str:
    raw = f"{anomaly_type}::{hub}::{carrier}".lower()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


class LongTermMemory:
    """SQLite-backed episodic memory and pattern registry."""

    def save_episode(self, episode: LongTermEpisode):
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO episodes
                (episode_id, timestamp, pattern_signature, context_json,
                 action_taken, outcome, confidence_delta)
                VALUES (?,?,?,?,?,?,?)
            """,
                (
                    episode.episode_id,
                    episode.timestamp,
                    episode.pattern_signature,
                    json.dumps(episode.context),
                    episode.action_taken,
                    episode.outcome,
                    episode.confidence_delta,
                ),
            )

    def recent_episodes(self, n: int = 20) -> list[dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (n,)
            ).fetchall()
        return [dict(r) for r in rows]

    def lookup_pattern(self, anomaly_type: str, hub: str, carrier: str) -> PatternRecord | None:
        sig = _sig(anomaly_type, hub, carrier)
        with get_db() as conn:
            row = conn.execute("SELECT * FROM patterns WHERE signature = ?", (sig,)).fetchone()
        if not row:
            return None
        return PatternRecord(
            signature=row["signature"],
            description=row["description"],
            occurrences=row["occurrences"],
            last_seen=row["last_seen"],
            avg_confidence=row["avg_confidence"],
            recommended_action=row["recommended_action"],
        )

    def upsert_pattern(
        self,
        anomaly_type: str,
        hub: str,
        carrier: str,
        description: str,
        outcome: str,
        recommended_action: str,
    ):
        sig = _sig(anomaly_type, hub, carrier)
        now = datetime.utcnow().isoformat()
        with get_db() as conn:
            existing = conn.execute(
                "SELECT occurrences, avg_confidence FROM patterns WHERE signature=?", (sig,)
            ).fetchone()
            if existing:
                new_occ = existing["occurrences"] + 1
                new_conf = (
                    existing["avg_confidence"] * existing["occurrences"]
                    + (1.0 if outcome == "SUCCESS" else 0.5)
                ) / new_occ
                conn.execute(
                    """
                    UPDATE patterns SET occurrences=?, last_seen=?, avg_confidence=?,
                    recommended_action=? WHERE signature=?
                """,
                    (new_occ, now, new_conf, recommended_action, sig),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO patterns
                    (signature, description, occurrences, last_seen, avg_confidence, recommended_action)
                    VALUES (?,?,1,?,0.75,?)
                """,
                    (sig, description, now, recommended_action),
                )

    def format_for_prompt(self, patterns: list[PatternRecord]) -> str:
        if not patterns:
            return "No matching historical patterns."
        parts = []
        for p in patterns:
            parts.append(
                f"- Pattern '{p.description}' seen {p.occurrences}x "
                f"(last: {p.last_seen}), confidence {p.avg_confidence:.0%}. "
                f"Recommended: {p.recommended_action}"
            )
        return "\n".join(parts)


long_term_memory = LongTermMemory()
