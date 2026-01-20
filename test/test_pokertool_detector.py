from __future__ import annotations

import time

import pytest

from actifix.modules.pokertool.detector import DetectionPipeline


def test_detection_pipeline_emits_updates() -> None:
    pipeline = DetectionPipeline(update_interval=0.05, history_size=5)
    try:
        pipeline.start()
        time.sleep(0.2)
        summary = pipeline.summary()
        assert summary["history_count"] >= 1
        assert pipeline.latest_update() is not None
    finally:
        pipeline.stop()


def test_detection_pipeline_prevents_double_start() -> None:
    pipeline = DetectionPipeline(update_interval=0.01)
    pipeline.start()
    with pytest.raises(RuntimeError):
        pipeline.start()
    pipeline.stop()


def test_detection_pipeline_inactive_after_stop() -> None:
    pipeline = DetectionPipeline(update_interval=0.02)
    pipeline.start()
    time.sleep(0.04)
    pipeline.stop()
    assert pipeline.active is False
