"""
Actifix AI Context Subsystem.

Provides long-lived context memory integrations (Letta) and
pluggable vector stores for retrieval augmentation.
"""

from .manager import AIContextManager, get_ai_context_manager, reset_ai_context_manager
from .memory_store import MemoryStore
from .models import MemoryRecord, VectorRecord
from .vector_store import VectorStore

__all__ = [
    "AIContextManager",
    "get_ai_context_manager",
    "reset_ai_context_manager",
    "MemoryRecord",
    "MemoryStore",
    "VectorRecord",
    "VectorStore",
]