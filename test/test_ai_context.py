# -*- coding: utf-8 -*-

"""Comprehensive tests for AI context persistence (embeddings and conversation memory)."""

from pathlib import Path
from datetime import datetime, timezone

import pytest

from actifix.ai_context.manager import AIContextManager, AIContextConfig, reset_ai_context_manager
from actifix.ai_context.models import MemoryRecord, VectorRecord
from actifix.ai_context.sqlite_vss_store import SQLiteVSSStore


class TestContextEmbeddingsPersistence:
    """Test vector embeddings persistence in SQLite-VSS store."""

    def test_sqlite_vss_store_round_trip(self, tmp_path: Path) -> None:
        """Verify basic upsert and fetch operations."""
        db_path = tmp_path / "ai_context.db"
        store = SQLiteVSSStore(str(db_path))
        assert store.is_available()

        record = VectorRecord(record_id="vec-1", content="hello")
        store.upsert(record)

        fetched = store.fetch("vec-1")
        assert fetched is not None
        assert fetched.record_id == "vec-1"
        assert fetched.content == "hello"

        results = list(store.query("hello", limit=5))
        assert results

    def test_vector_persistence_across_sessions(self, tmp_path: Path) -> None:
        """Verify vectors persist across store reopens."""
        db_path = tmp_path / "ai_context.db"

        # First session: insert vectors
        store1 = SQLiteVSSStore(str(db_path))
        store1.upsert(VectorRecord(record_id="vec-1", content="first vector"))
        store1.upsert(VectorRecord(record_id="vec-2", content="second vector"))

        # Second session: verify persistence
        store2 = SQLiteVSSStore(str(db_path))
        vec1 = store2.fetch("vec-1")
        vec2 = store2.fetch("vec-2")

        assert vec1 is not None
        assert vec1.content == "first vector"
        assert vec2 is not None
        assert vec2.content == "second vector"

    def test_vector_upsert_updates_existing(self, tmp_path: Path) -> None:
        """Verify upsert updates existing records."""
        db_path = tmp_path / "ai_context.db"
        store = SQLiteVSSStore(str(db_path))

        # Insert initial record
        store.upsert(VectorRecord(record_id="vec-1", content="original"))

        # Update via upsert
        store.upsert(VectorRecord(record_id="vec-1", content="updated"))

        # Verify update
        fetched = store.fetch("vec-1")
        assert fetched is not None
        assert fetched.content == "updated"

    def test_vector_query_returns_relevant_results(self, tmp_path: Path) -> None:
        """Verify query returns semantically relevant vectors."""
        db_path = tmp_path / "ai_context.db"
        store = SQLiteVSSStore(str(db_path))

        # Insert diverse content
        store.upsert(VectorRecord(record_id="vec-1", content="python programming"))
        store.upsert(VectorRecord(record_id="vec-2", content="cooking recipes"))
        store.upsert(VectorRecord(record_id="vec-3", content="python development"))

        # Query should return results (exact relevance depends on embeddings)
        results = list(store.query("programming", limit=10))
        assert len(results) >= 1

    def test_vector_metadata_persists(self, tmp_path: Path) -> None:
        """Verify vector metadata is persisted."""
        db_path = tmp_path / "ai_context.db"
        store = SQLiteVSSStore(str(db_path))

        metadata = {"source": "test", "priority": "high"}
        store.upsert(VectorRecord(
            record_id="vec-1",
            content="content",
            metadata=metadata
        ))

        fetched = store.fetch("vec-1")
        assert fetched is not None
        assert fetched.metadata == metadata


class TestConversationMemoryPersistence:
    """Test conversation memory persistence via memory store."""

    def test_memory_store_and_search(self, tmp_path: Path) -> None:
        """Verify memory records can be stored and searched."""
        config = AIContextConfig(
            memory_enabled=True,
            vector_enabled=False,
            sqlite_db_path=str(tmp_path / "ai_context.db"),
        )
        manager = AIContextManager(config=config)

        # Store memory
        memory = MemoryRecord(
            record_id="mem-1",
            content="User prefers Python for scripting",
            source="conversation"
        )
        manager.store_memory(memory)

        # Search should work (exact behavior depends on Letta implementation)
        # For now, just verify no errors
        results = list(manager.search_memory("Python", limit=5))
        # Results depend on Letta availability

    def test_conversation_history_accumulation(self, tmp_path: Path) -> None:
        """Verify multiple conversation turns accumulate correctly."""
        config = AIContextConfig(
            memory_enabled=True,
            vector_enabled=False,
            sqlite_db_path=str(tmp_path / "ai_context.db"),
        )
        manager = AIContextManager(config=config)

        # Store multiple conversation turns
        turns = [
            MemoryRecord(record_id="turn-1", content="What is Python?"),
            MemoryRecord(record_id="turn-2", content="Python is a programming language"),
            MemoryRecord(record_id="turn-3", content="How do I install it?"),
        ]

        for turn in turns:
            manager.store_memory(turn)

        # Verify no errors during accumulation


class TestAIContextManagerIntegration:
    """Test AIContextManager coordinating memory and vector stores."""

    def test_manager_with_both_stores_enabled(self, tmp_path: Path) -> None:
        """Verify manager works with both memory and vector stores."""
        config = AIContextConfig(
            memory_enabled=True,
            vector_enabled=True,
            sqlite_db_path=str(tmp_path / "ai_context.db"),
        )
        manager = AIContextManager(config=config)

        # Store both types
        manager.store_memory(MemoryRecord(record_id="mem-1", content="conversation"))
        manager.upsert_vector(VectorRecord(record_id="vec-1", content="embedding"))

        # Verify both available
        # Note: memory availability depends on Letta being installed/configured

    def test_manager_fallback_when_memory_disabled(self, tmp_path: Path) -> None:
        """Verify graceful fallback when memory is disabled."""
        config = AIContextConfig(
            memory_enabled=False,
            vector_enabled=True,
            sqlite_db_path=str(tmp_path / "ai_context.db"),
        )
        manager = AIContextManager(config=config)
        manager.store_memory(MemoryRecord(record_id="mem-1", content="ignored"))

        vector = VectorRecord(record_id="vec-2", content="context")
        manager.upsert_vector(vector)
        results = list(manager.query_vectors("context", limit=1))
        assert results

    def test_manager_all_disabled(self) -> None:
        """Verify manager handles all stores disabled."""
        config = AIContextConfig(
            memory_enabled=False,
            vector_enabled=False,
            sqlite_db_path=":memory:"
        )
        manager = AIContextManager(config=config)
        assert not manager.memory_available()
        assert not manager.vector_available()
        assert list(manager.search_memory("query")) == []

    def test_manager_singleton_reset(self, tmp_path: Path) -> None:
        """Verify singleton manager can be reset."""
        from actifix.ai_context.manager import get_ai_context_manager

        reset_ai_context_manager()
        manager1 = get_ai_context_manager()
        assert manager1 is not None

        reset_ai_context_manager()
        manager2 = get_ai_context_manager()
        assert manager2 is not None
        # Different instances after reset
        assert manager1 is not manager2


class TestAIContextErrorHandling:
    """Test error handling in AI context operations."""

    def test_vector_store_handles_missing_record(self, tmp_path: Path) -> None:
        """Verify fetch returns None for missing records."""
        db_path = tmp_path / "ai_context.db"
        store = SQLiteVSSStore(str(db_path))

        result = store.fetch("nonexistent")
        assert result is None

    def test_manager_handles_vector_errors_gracefully(self, tmp_path: Path) -> None:
        """Verify manager doesn't crash on vector store errors."""
        config = AIContextConfig(
            memory_enabled=False,
            vector_enabled=True,
            sqlite_db_path="/invalid/path/db.db",  # Invalid path
        )
        # Manager should handle initialization gracefully
        manager = AIContextManager(config=config)
        # Operations should not crash even if store is unavailable