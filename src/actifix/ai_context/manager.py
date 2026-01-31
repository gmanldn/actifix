from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .letta_store import LettaMemoryStore
from .memory_store import MemoryStore
from .models import MemoryRecord, VectorRecord
from .sqlite_vss_store import SQLiteVSSStore
from .vector_store import VectorStore
from ..config import get_config
from ..raise_af import record_error, TicketPriority
from ..state_paths import get_actifix_paths


@dataclass
class AIContextConfig:
    memory_enabled: bool
    vector_enabled: bool
    sqlite_db_path: str


class AIContextManager:
    """Coordinate AI memory and vector stores with graceful fallback."""

    def __init__(self, config: Optional[AIContextConfig] = None) -> None:
        self._config = config or self._load_config()
        self._memory_store: MemoryStore = LettaMemoryStore()
        self._vector_store: VectorStore = SQLiteVSSStore(self._config.sqlite_db_path)

    def _load_config(self) -> AIContextConfig:
        config = get_config()
        paths = get_actifix_paths()
        sqlite_path = str(paths.data_dir / "ai_context.db")
        return AIContextConfig(
            memory_enabled=bool(getattr(config, "ai_memory_enabled", True)),
            vector_enabled=bool(getattr(config, "ai_vector_store_enabled", True)),
            sqlite_db_path=str(getattr(config, "ai_vector_store_path", sqlite_path)),
        )

    def memory_available(self) -> bool:
        return self._config.memory_enabled and self._memory_store.is_available()

    def vector_available(self) -> bool:
        return self._config.vector_enabled and self._vector_store.is_available()

    def store_memory(self, record: MemoryRecord) -> None:
        if not self._config.memory_enabled:
            return
        try:
            # Apply redaction before storing to AI context
            from ..raise_af import redact_secrets_from_text
            redacted_record = MemoryRecord(
                id=record.id,
                content=redact_secrets_from_text(record.content),
                metadata=record.metadata,
                timestamp=record.timestamp,
            )
            self._memory_store.store(redacted_record)
        except Exception as exc:
            record_error(
                message=f"AI memory store failed: {exc}",
                source="ai_context/manager.py:store_memory",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )

    def search_memory(self, query: str, limit: int = 5) -> Iterable[MemoryRecord]:
        if not self._config.memory_enabled:
            return []
        try:
            return self._memory_store.search(query, limit=limit)
        except Exception as exc:
            record_error(
                message=f"AI memory search failed: {exc}",
                source="ai_context/manager.py:search_memory",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return []

    def upsert_vector(self, record: VectorRecord) -> None:
        if not self._config.vector_enabled:
            return
        try:
            # Apply redaction before storing to AI context
            from ..raise_af import redact_secrets_from_text
            redacted_record = VectorRecord(
                id=record.id,
                content=redact_secrets_from_text(record.content),
                embedding=record.embedding,
                metadata=record.metadata,
            )
            self._vector_store.upsert(redacted_record)
        except Exception as exc:
            record_error(
                message=f"AI vector upsert failed: {exc}",
                source="ai_context/manager.py:upsert_vector",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )

    def query_vectors(self, query: str, limit: int = 5) -> Iterable[VectorRecord]:
        if not self._config.vector_enabled:
            return []
        try:
            return self._vector_store.query(query, limit=limit)
        except Exception as exc:
            record_error(
                message=f"AI vector query failed: {exc}",
                source="ai_context/manager.py:query_vectors",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return []


_ai_context_manager: Optional[AIContextManager] = None


def get_ai_context_manager() -> AIContextManager:
    global _ai_context_manager
    if _ai_context_manager is None:
        _ai_context_manager = AIContextManager()
    return _ai_context_manager


def reset_ai_context_manager() -> None:
    global _ai_context_manager
    _ai_context_manager = None