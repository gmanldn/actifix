from __future__ import annotations

from typing import Iterable, Optional

from .memory_store import MemoryStore
from .models import MemoryRecord
from ..raise_af import record_error, TicketPriority


class LettaMemoryStore(MemoryStore):
    """Adapter for Letta (MemGPT) long-term memory."""

    def __init__(self) -> None:
        self._client = None
        self._init_error: Optional[str] = None
        self._ensure_client()

    def _ensure_client(self) -> None:
        if self._client is not None or self._init_error is not None:
            return
        try:
            import letta  # type: ignore

            self._client = letta.Client()
        except Exception as exc:
            self._init_error = str(exc)
            record_error(
                message=f"Letta client init failed: {exc}",
                source="ai_context/letta_store.py:LettaMemoryStore",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )

    def is_available(self) -> bool:
        self._ensure_client()
        return self._client is not None

    def store(self, record: MemoryRecord) -> None:
        if not self.is_available():
            raise RuntimeError("Letta client unavailable")
        try:
            payload = {
                "content": record.content,
                "metadata": record.metadata,
                "source": record.source,
                "record_id": record.record_id,
                "created_at": record.created_at.isoformat(),
            }
            self._client.store_memory(payload)
        except Exception as exc:
            record_error(
                message=f"Letta store failed: {exc}",
                source="ai_context/letta_store.py:store",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            raise

    def fetch(self, record_id: str) -> Optional[MemoryRecord]:
        if not self.is_available():
            return None
        try:
            payload = self._client.get_memory(record_id)
            if not payload:
                return None
            return MemoryRecord(
                record_id=payload.get("record_id", record_id),
                content=payload.get("content", ""),
                metadata=payload.get("metadata", {}) or {},
                source=payload.get("source", ""),
            )
        except Exception as exc:
            record_error(
                message=f"Letta fetch failed: {exc}",
                source="ai_context/letta_store.py:fetch",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return None

    def search(self, query: str, limit: int = 5) -> Iterable[MemoryRecord]:
        if not self.is_available():
            return []
        try:
            results = self._client.search_memory(query, limit=limit)
            records = []
            for item in results or []:
                records.append(
                    MemoryRecord(
                        record_id=item.get("record_id", ""),
                        content=item.get("content", ""),
                        metadata=item.get("metadata", {}) or {},
                        source=item.get("source", ""),
                    )
                )
            return records
        except Exception as exc:
            record_error(
                message=f"Letta search failed: {exc}",
                source="ai_context/letta_store.py:search",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )
            return []