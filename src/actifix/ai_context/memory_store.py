from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .models import MemoryRecord


class MemoryStore(ABC):
    """Abstract interface for long-lived AI memory stores."""

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def store(self, record: MemoryRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, record_id: str) -> Optional[MemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> Iterable[MemoryRecord]:
        raise NotImplementedError