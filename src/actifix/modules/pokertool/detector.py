"""Detection pipeline helpers for the PokerTool module."""

from __future__ import annotations

import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Sequence

from actifix.log_utils import log_event


@dataclass(frozen=True)
class DetectionUpdate:
    sequence: int
    timestamp: float
    table_state: dict[str, object]
    confidence: float
    notes: Sequence[str]


class DetectionPipeline:
    """Lightweight detection runner that emits mock table states."""

    def __init__(self, update_interval: float = 0.8, history_size: int = 12) -> None:
        self._interval = max(update_interval, 0.1)
        self._history: Deque[DetectionUpdate] = deque(maxlen=history_size)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._sequence = 0

    @property
    def active(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        with self._lock:
            if self.active:
                raise RuntimeError("Detection pipeline already running.")
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            log_event("POKERTOOL_DETECTOR_START", "Detection pipeline started.")

    def stop(self) -> None:
        with self._lock:
            if not self.active:
                return
            self._stop_event.set()
            thread = self._thread
        if thread:
            thread.join(timeout=2.0)
        log_event("POKERTOOL_DETECTOR_STOP", "Detection pipeline stopped.")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            update = self._build_update()
            with self._lock:
                self._history.append(update)
            time.sleep(self._interval)

    def _build_update(self) -> DetectionUpdate:
        cards = self._mock_table_state()
        confidence = round(random.uniform(0.6, 0.95), 2)
        notes = [f"Confidence {confidence * 100:.0f}%", "State captured via mock detector"]
        update = DetectionUpdate(
            sequence=self._sequence,
            timestamp=time.time(),
            table_state=cards,
            confidence=confidence,
            notes=notes,
        )
        self._sequence += 1
        return update

    def _mock_table_state(self) -> dict[str, object]:
        players = [
            {"seat": idx + 1, "stack": round(random.uniform(50, 150), 1)}
            for idx in range(2)
        ]
        board = random.sample(["Ah", "Kd", "Qs", "Jc", "10h", "9d"], k=3)
        action = random.choice(["raise", "fold", "call", "check"])
        return {
            "players": players,
            "board": board,
            "action": action,
            "timestamp": time.time(),
        }

    def latest_update(self) -> DetectionUpdate | None:
        with self._lock:
            return self._history[-1] if self._history else None

    def history(self) -> list[DetectionUpdate]:
        with self._lock:
            return list(self._history)

    def summary(self) -> dict[str, object]:
        with self._lock:
            latest = self._history[-1] if self._history else None
            return {
                "active": self.active,
                "history_count": len(self._history),
                "last_sequence": latest.sequence if latest else None,
                "last_confidence": latest.confidence if latest else None,
            }

    def payload_for(self, detail: DetectionUpdate | None) -> dict[str, object]:
        if not detail:
            return {}
        return {
            "sequence": detail.sequence,
            "timestamp": detail.timestamp,
            "confidence": detail.confidence,
            "table_state": detail.table_state,
            "notes": list(detail.notes),
        }
