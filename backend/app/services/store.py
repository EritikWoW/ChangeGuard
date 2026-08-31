import json
import sqlite3
from datetime import datetime
from app.core.config import settings
from app.models.schemas import AnalysisResponse, AnalysisListItem


class AnalysisStore:
    def __init__(self) -> None:
        self.path = settings.db_path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    repo TEXT NOT NULL,
                    pull_request INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
            """)
            conn.commit()

    def save(self, analysis: AnalysisResponse) -> None:
        payload = analysis.model_dump_json()
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO analyses(id,repo,pull_request,title,decision,severity,confidence,created_at,payload)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    repo=excluded.repo,pull_request=excluded.pull_request,title=excluded.title,
                    decision=excluded.decision,severity=excluded.severity,confidence=excluded.confidence,
                    created_at=excluded.created_at,payload=excluded.payload
            """, (
                analysis.id, analysis.repo, analysis.pull_request, analysis.title,
                analysis.decision.value, analysis.severity.value, analysis.confidence,
                analysis.created_at.isoformat(), payload
            ))
            conn.commit()

    def get(self, analysis_id: str) -> AnalysisResponse | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        return AnalysisResponse.model_validate_json(row["payload"]) if row else None

    def list_full(self, limit: int = 50) -> list[AnalysisResponse]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM analyses ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [AnalysisResponse.model_validate_json(row["payload"]) for row in rows]

    def list(self, limit: int = 50) -> list[AnalysisListItem]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id,repo,pull_request,title,decision,severity,confidence,created_at FROM analyses ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [AnalysisListItem.model_validate(dict(row)) for row in rows]


store = AnalysisStore()
