import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import settings


def init_db():
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                episode_id        TEXT PRIMARY KEY,
                timestamp         TEXT,
                pattern_signature TEXT,
                context_json      TEXT,
                action_taken      TEXT,
                outcome           TEXT,
                confidence_delta  REAL
            );
            CREATE TABLE IF NOT EXISTS patterns (
                signature          TEXT PRIMARY KEY,
                description        TEXT,
                occurrences        INTEGER DEFAULT 0,
                last_seen          TEXT,
                avg_confidence     REAL DEFAULT 0.75,
                recommended_action TEXT
            );
            CREATE TABLE IF NOT EXISTS approvals (
                id            TEXT PRIMARY KEY,
                shipment_id   TEXT,
                action        TEXT,
                details_json  TEXT,
                status        TEXT DEFAULT 'pending',
                created_at    TEXT,
                resolved_at   TEXT
            );
            CREATE TABLE IF NOT EXISTS action_log (
                id           TEXT PRIMARY KEY,
                cycle_id     TEXT,
                timestamp    TEXT,
                action_type  TEXT,
                target       TEXT,
                params_json  TEXT,
                outcome      TEXT
            );
        """
        )


@contextmanager
def get_db():
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
