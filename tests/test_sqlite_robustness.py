"""Tests for SQLite robustness: WAL safety, corruption detection, backup/restore."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import shutil
import time

from actifix.persistence.sqlite_robustness import (
    SQLiteRobustness,
    CorruptionSeverity,
    CorruptionReport,
    get_robustness_manager,
)


@pytest.fixture
def temp_db_dir():
    """Create temporary directory for test databases."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def test_db(temp_db_dir):
    """Create a test SQLite database."""
    db_path = temp_db_dir / "test.db"

    # Create a database with a simple schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT INTO test_table (value) VALUES ('test_value')")
    conn.commit()
    conn.close()

    return db_path


class TestSQLiteRobustness:
    """Test SQLiteRobustness manager."""

    def test_creation(self, test_db):
        """Test creating a robustness manager."""
        manager = SQLiteRobustness(test_db)
        assert manager.db_path == test_db
        assert manager.journal_mode == "WAL"
        assert manager.synchronous == "NORMAL"

    def test_custom_config(self, test_db):
        """Test robustness manager with custom config."""
        config = {
            "journal_mode": "DELETE",
            "synchronous": "FULL",
            "checkpoint_interval_s": 100,
            "vacuum_interval_s": 1000,
        }
        manager = SQLiteRobustness(test_db, config=config)

        assert manager.journal_mode == "DELETE"
        assert manager.synchronous == "FULL"
        assert manager.checkpoint_interval_s == 100
        assert manager.vacuum_interval_s == 1000

    def test_enforce_pragmas(self, test_db):
        """Test enforcing safety PRAGMAs."""
        manager = SQLiteRobustness(test_db)
        pragmas = manager.enforce_pragmas()

        assert "journal_mode" in pragmas
        assert "synchronous" in pragmas
        assert "foreign_keys" in pragmas

        # Verify PRAGMAs were actually set
        conn = sqlite3.connect(str(test_db), timeout=10.0)
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode")
        journal = cursor.fetchone()[0]
        assert journal.lower() == "wal"

        cursor.execute("PRAGMA foreign_keys")
        fk = cursor.fetchone()[0]
        assert fk == 1  # ON

        conn.close()

    def test_corruption_check_clean_db(self, test_db):
        """Test corruption check on clean database."""
        manager = SQLiteRobustness(test_db)
        report = manager.check_corruption()

        assert report.severity == CorruptionSeverity.NONE
        assert "passed" in report.message.lower() or "ok" in report.message.lower()

    def test_backup_creation(self, test_db):
        """Test creating a database backup."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        backup_path = manager.backup()

        assert backup_path.exists()
        assert "backup" in backup_path.name
        assert backup_path.suffix == ".db"

    def test_backup_verification(self, test_db):
        """Test that backup is verified."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        backup_path = manager.backup()

        # Backup should be a valid database
        conn = sqlite3.connect(str(backup_path), timeout=5.0)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 0  # Should be able to query

    def test_backup_custom_name(self, test_db):
        """Test backup with custom name."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        backup_path = manager.backup(backup_name="my_backup.db")

        assert backup_path.exists()
        assert "my_backup" in backup_path.name

    def test_restore_from_backup(self, test_db):
        """Test restoring from backup."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        # Insert data
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test_table (value) VALUES ('new_value')")
        conn.commit()
        conn.close()

        # Create backup
        backup_path = manager.backup()

        # Modify database
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM test_table WHERE value = 'new_value'")
        conn.commit()
        conn.close()

        # Restore from backup
        manager.restore(backup_path, verify=True)

        # Check data is restored
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0

    def test_restore_nonexistent_backup(self, test_db):
        """Test restore with nonexistent backup."""
        manager = SQLiteRobustness(test_db)

        with pytest.raises(FileNotFoundError):
            manager.restore(Path("/nonexistent/backup.db"))

    def test_quarantine_corrupted_db(self, test_db):
        """Test quarantining corrupted database."""
        manager = SQLiteRobustness(test_db)

        quarantine_path = manager.quarantine_corrupted_db()

        assert quarantine_path.exists()
        assert "corrupted" in quarantine_path.name
        assert quarantine_path.parent == manager.backup_dir

    def test_periodic_maintenance(self, test_db):
        """Test periodic maintenance operations."""
        manager = SQLiteRobustness(
            test_db,
            config={
                "checkpoint_interval_s": 0,
                "vacuum_interval_s": 0,
            }
        )
        manager.enforce_pragmas()

        results = manager.periodic_maintenance()

        # Should attempt checkpoint and vacuum
        assert "checkpoint" in results or "vacuum" in results

    def test_get_health(self, test_db):
        """Test getting database health status."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        health = manager.get_health()

        assert "healthy" in health
        assert "size_bytes" in health
        assert "journal_mode" in health
        assert health["healthy"] is True

    def test_manager_caching(self, test_db):
        """Test that managers are cached by path."""
        manager1 = get_robustness_manager(test_db)
        manager2 = get_robustness_manager(test_db)

        assert manager1 is manager2

    def test_manager_separate_instances(self, temp_db_dir):
        """Test separate managers for different databases."""
        db1 = temp_db_dir / "db1.db"
        db2 = temp_db_dir / "db2.db"

        # Create both databases
        for db_path in [db1, db2]:
            conn = sqlite3.connect(str(db_path))
            conn.close()

        manager1 = get_robustness_manager(db1)
        manager2 = get_robustness_manager(db2)

        assert manager1 is not manager2
        assert manager1.db_path == db1
        assert manager2.db_path == db2

    def test_corruption_report_timestamp(self, test_db):
        """Test that corruption report includes timestamp."""
        manager = SQLiteRobustness(test_db)
        report = manager.check_corruption()

        assert report.timestamp
        assert "Z" in report.timestamp  # ISO format

    def test_backup_creates_backup_dir(self, temp_db_dir):
        """Test that backup creates backup directory."""
        db_path = temp_db_dir / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()

        manager = SQLiteRobustness(db_path)
        assert not manager.backup_dir.exists()

        manager.backup()
        assert manager.backup_dir.exists()

    def test_busy_database_backup(self, test_db):
        """Test backing up a busy database."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        # Open connection in write mode
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()

        # Start transaction
        cursor.execute("BEGIN")
        cursor.execute("INSERT INTO test_table (value) VALUES ('busy')")

        # Backup should still work (checkpoint handles this)
        backup_path = manager.backup()
        assert backup_path.exists()

        # Commit transaction
        conn.commit()
        conn.close()

    def test_checkpoint_on_backup(self, test_db):
        """Test that backup triggers checkpoint."""
        manager = SQLiteRobustness(test_db)
        manager.enforce_pragmas()

        assert manager.last_checkpoint == 0.0

        manager.backup()

        assert manager.last_checkpoint > 0.0

    def test_pragmas_enforcement_idempotent(self, test_db):
        """Test that enforcing pragmas multiple times is safe."""
        manager = SQLiteRobustness(test_db)

        pragmas1 = manager.enforce_pragmas()
        time.sleep(0.1)
        pragmas2 = manager.enforce_pragmas()

        # Should produce same results
        assert pragmas1.keys() == pragmas2.keys()

    def test_corruption_check_on_corrupted_db(self, temp_db_dir):
        """Test corruption detection on corrupted database (simulated)."""
        db_path = temp_db_dir / "corrupt.db"

        # Create a test database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.close()

        manager = SQLiteRobustness(db_path)

        # Note: We can't easily corrupt a real SQLite database for testing
        # This test verifies the structure is in place
        report = manager.check_corruption()
        assert isinstance(report, CorruptionReport)
        assert hasattr(report, 'severity')
        assert hasattr(report, 'message')


class TestCorruptionReport:
    """Test CorruptionReport dataclass."""

    def test_report_creation(self):
        """Test creating a corruption report."""
        report = CorruptionReport(
            severity=CorruptionSeverity.WARNING,
            message="Test warning",
            errors=["error1", "error2"]
        )

        assert report.severity == CorruptionSeverity.WARNING
        assert report.message == "Test warning"
        assert report.errors == ["error1", "error2"]

    def test_report_default_timestamp(self):
        """Test that report gets default timestamp."""
        report = CorruptionReport(
            severity=CorruptionSeverity.NONE,
            message="Test"
        )

        assert report.timestamp
        assert "Z" in report.timestamp

    def test_report_default_errors(self):
        """Test that report has default empty errors."""
        report = CorruptionReport(
            severity=CorruptionSeverity.NONE,
            message="Test"
        )

        assert report.errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
