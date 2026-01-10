#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Concurrency tests for DoAF ticket processing.
"""

import threading
from pathlib import Path

import pytest

from actifix.raise_af import record_error, ACTIFIX_CAPTURE_ENV_VAR
from actifix.do_af import process_next_ticket, get_ticket_stats
from actifix.state_paths import get_actifix_paths, reset_actifix_paths


def test_process_next_ticket_thread_safe(tmp_path, monkeypatch):
    """Multiple threads should not dispatch the same ticket."""
    # Isolate Actifix dirs
    reset_actifix_paths()
    paths = get_actifix_paths(base_dir=tmp_path / "actifix")
    monkeypatch.setenv(ACTIFIX_CAPTURE_ENV_VAR, "1")
    
    # Generate a small set of tickets
    labels = ["alpha", "bravo", "charlie", "delta", "echo"]
    for label in labels:
        record_error(
            message=f"Concurrent ticket {label}",
            source="do_af_concurrency.py",
            run_label="concurrency",
            error_type="ConcurrencyTest",
            paths=paths,
            capture_context=False,
            skip_ai_notes=True,
        )
    
    processed_ids: set[str] = set()
    lock = threading.Lock()
    
    def worker():
        while True:
            ticket = process_next_ticket(ai_handler=lambda t: True, paths=paths)
            if not ticket:
                break
            with lock:
                processed_ids.add(ticket.ticket_id)
    
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    stats = get_ticket_stats(paths)
    assert stats["open"] == 0
    assert len(processed_ids) == 5
