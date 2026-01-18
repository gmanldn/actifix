#!/usr/bin/env python3
"""
Database operation profiler for test performance analysis.

Tracks database queries, connection times, and transaction overhead.
Helps identify database bottlenecks in test suite.
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseOperation:
    """Record of a single database operation."""

    operation_type: str  # SELECT, INSERT, UPDATE, DELETE, TRANSACTION, etc.
    query: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    connection_id: Optional[int] = None


class DatabaseProfiler:
    """Profiles database operations during tests."""

    def __init__(self):
        """Initialize database profiler."""
        self.operations: List[DatabaseOperation] = []
        self.connection_count = 0
        self.transaction_count = 0
        self.query_count = 0

    def record_operation(self, operation: DatabaseOperation):
        """Record a database operation."""
        self.operations.append(operation)

        if "TRANSACTION" in operation.operation_type:
            self.transaction_count += 1
        elif "SELECT" in operation.operation_type.upper():
            self.query_count += 1

    def record_connection(self):
        """Record a database connection."""
        self.connection_count += 1

    def get_stats(self) -> Dict:
        """Get profiling statistics."""
        if not self.operations:
            return {
                "total_operations": 0,
                "total_time_ms": 0,
                "avg_operation_ms": 0,
                "connections": 0,
                "transactions": 0,
                "queries": 0,
            }

        total_time = sum(op.duration_ms for op in self.operations)
        avg_time = total_time / len(self.operations)

        operation_types = {}
        for op in self.operations:
            op_type = op.operation_type.split()[0] if op.operation_type else "UNKNOWN"
            if op_type not in operation_types:
                operation_types[op_type] = {"count": 0, "total_ms": 0}
            operation_types[op_type]["count"] += 1
            operation_types[op_type]["total_ms"] += op.duration_ms

        return {
            "total_operations": len(self.operations),
            "total_time_ms": total_time,
            "avg_operation_ms": avg_time,
            "connections": self.connection_count,
            "transactions": self.transaction_count,
            "queries": self.query_count,
            "by_type": operation_types,
            "slowest_operations": sorted(
                self.operations, key=lambda x: x.duration_ms, reverse=True
            )[:10],
        }

    def report(self):
        """Generate database profiling report."""
        stats = self.get_stats()

        if stats["total_operations"] == 0:
            return

        print("\n" + "=" * 80)
        print("DATABASE PROFILING ANALYSIS")
        print("=" * 80)
        print(f"Total Operations:     {stats['total_operations']}")
        print(f"Total Time:           {stats['total_time_ms']:.1f}ms")
        print(f"Avg Operation Time:   {stats['avg_operation_ms']:.2f}ms")
        print(f"Connections:          {stats['connections']}")
        print(f"Transactions:         {stats['transactions']}")
        print(f"Queries:              {stats['queries']}")
        print()

        if stats["by_type"]:
            print("OPERATIONS BY TYPE:")
            print("-" * 80)
            for op_type, data in sorted(
                stats["by_type"].items(), key=lambda x: x[1]["total_ms"], reverse=True
            ):
                print(
                    f"  {op_type:15s}: {data['count']:4d} ops, {data['total_ms']:8.1f}ms total, "
                    f"{data['total_ms'] / data['count']:7.2f}ms avg"
                )

        if stats["slowest_operations"]:
            print("\nTOP 10 SLOWEST OPERATIONS:")
            print("-" * 80)
            for i, op in enumerate(stats["slowest_operations"], 1):
                query_preview = op.query[:50].replace("\n", " ")
                print(f"{i:2d}. {op.duration_ms:7.2f}ms | {query_preview}...")

        print("=" * 80)


# Global profiler instance
_db_profiler = DatabaseProfiler()


def get_database_profiler() -> DatabaseProfiler:
    """Get the global database profiler instance."""
    return _db_profiler


def reset_database_profiler():
    """Reset the database profiler (for testing)."""
    global _db_profiler
    _db_profiler = DatabaseProfiler()


@contextmanager
def profile_db_operation(operation_type: str, query: str = ""):
    """Context manager to profile a database operation."""
    start_time = time.time()
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        operation = DatabaseOperation(
            operation_type=operation_type,
            query=query,
            duration_ms=duration_ms,
        )
        _db_profiler.record_operation(operation)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        operation = DatabaseOperation(
            operation_type=operation_type,
            query=query,
            duration_ms=duration_ms,
            error=str(e),
        )
        _db_profiler.record_operation(operation)
        raise
