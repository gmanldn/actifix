from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .models import VectorRecord


class VectorStore(ABC):
    """Abstract interface for vector store backends."""

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, record: VectorRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, record_id: str) -> Optional[VectorRecord]:
        raise NotImplementedError

    @abstractmethod
    def query(self, query: str, limit: int = 5) -> Iterable[VectorRecord]:
        raise NotImplementedError