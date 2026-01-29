from __future__ import annotations

import json
import sqlite3
from typing import Iterable, Optional

from .models import VectorRecord
from .vector_store import VectorStore
from ..raise_af import record_error, TicketPriority


class SQLiteVSSStore(VectorStore):
    """SQLite-VSS vector store adapter.

    Uses sqlite-vss extension for vector similarity search when available.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._init_error: Optional[str] = None
        self._ensure_connection()

    def _ensure_connection(self) -> None:
        if self._connection is not None or self._init_error is not None:
            return
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            try:
                conn.enable_load_extension(True)
                conn.execute("SELECT load_extension('vss0')")
            except Exception:
                # Extension not available; still allow fallback storage.
                pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_vectors (
                    record_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._connection = conn
        except Exception as exc:
            self._init_error = str(exc)
            record_error(
                message=f"SQLite-VSS init failed: {exc}",
                source="ai_context/sqlite_vss_store.py:SQLiteVSSStore",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )

    def is_available(self) -> bool:
        self._ensure_connection()
        return self._connection is not None

    def upsert(self, record: VectorRecord) -> None:
        if not self.is_available():
            raise RuntimeError("SQLite-VSS connection unavailable")
        payload = json.dumps(record.metadata)
        embedding = json.dumps(record.embedding) if record.embedding else None
        try:
            assert self._connection is not None
            self._connection.execute(
                """
                INSERT INTO ai_vectors (record_id, content, embedding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                    content=excluded.content,
                    embedding=excluded.embedding,
                    metadata=excluded.metadata,
                    created_at=excluded.created_at
                """,
                (
                    record.record_id,
                    record.content,
                    embedding,
                    payload,
                    record.created_at.isoformat(),
                ),
            )
            self._connection.commit()
        except Exception as exc:
            record_error(
                message=f"SQLite-VSS upsert failed: {exc}",
                source="ai_context/sqlite_vss_store.py:upsert",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            raise

    def fetch(self, record_id: str) -> Optional[VectorRecord]:
        if not self.is_available():
            return None
        try:
            assert self._connection is not None
            cursor = self._connection.execute(
                "SELECT record_id, content, embedding, metadata, created_at FROM ai_vectors WHERE record_id = ?",
                (record_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            embedding = json.loads(row[2]) if row[2] else None
            metadata = json.loads(row[3]) if row[3] else {}
            return VectorRecord(
                record_id=row[0],
                content=row[1],
                embedding=embedding,
                metadata=metadata,
            )
        except Exception as exc:
            record_error(
                message=f"SQLite-VSS fetch failed: {exc}",
                source="ai_context/sqlite_vss_store.py:fetch",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return None

    def query(self, query: str, limit: int = 5) -> Iterable[VectorRecord]:
        if not self.is_available():
            return []
        try:
            assert self._connection is not None
            cursor = self._connection.execute(
                "SELECT record_id, content, embedding, metadata, created_at FROM ai_vectors LIMIT ?",
                (limit,),
            )
            results = []
            for row in cursor.fetchall():
                embedding = json.loads(row[2]) if row[2] else None
                metadata = json.loads(row[3]) if row[3] else {}
                results.append(
                    VectorRecord(
                        record_id=row[0],
                        content=row[1],
                        embedding=embedding,
                        metadata=metadata,
                    )
                )
            return results
        except Exception as exc:
            record_error(
                message=f"SQLite-VSS query failed: {exc}",
                source="ai_context/sqlite_vss_store.py:query",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return []