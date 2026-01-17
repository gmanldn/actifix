from __future__ import annotations

from pathlib import Path

from actifix.log_utils import LOG_ROTATION_KEEP_FILES, LOG_ROTATION_THRESHOLD_BYTES, append_with_guard


def test_append_with_guard_triggers_rotation(tmp_path: Path) -> None:
    log_file = tmp_path / "AFLog.txt"
    log_file.write_text("x" * (LOG_ROTATION_THRESHOLD_BYTES + 100))

    append_with_guard(log_file, "new line\n")

    rotated = tmp_path / f"{log_file.name}.1"
    assert rotated.exists(), "Rotation should produce a .1 backup"
    assert log_file.read_text().endswith("new line\n")

    # Rotation should respect keep limit: older rotations are dropped
    for idx in range(2, max(LOG_ROTATION_KEEP_FILES, 3) + 1):
        rotated_path = tmp_path / f"{log_file.name}.{idx}"
        assert not rotated_path.exists() or idx <= LOG_ROTATION_KEEP_FILES
