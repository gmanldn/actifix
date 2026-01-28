import argparse

from actifix.main import cmd_logs
from actifix.persistence.event_repo import EventRepository


def test_logs_tail_outputs_events(capsys):
    repo = EventRepository()
    repo.log_event(
        event_type="TEST_EVENT",
        message="hello logs",
        level="INFO",
        source="test",
    )

    args = argparse.Namespace(
        project_root=None,
        logs_action="tail",
        limit=5,
        level=None,
        event_type=None,
        source=None,
        ticket_id=None,
        correlation_id=None,
    )
    result = cmd_logs(args)
    captured = capsys.readouterr().out

    assert result == 0
    assert "TEST_EVENT" in captured
    assert "hello logs" in captured
