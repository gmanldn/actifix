import argparse

from actifix.main import cmd_config


def test_config_diff_shows_overrides(monkeypatch, capsys):
    monkeypatch.setenv("ACTIFIX_SLA_P0_HOURS", "2")

    args = argparse.Namespace(
        project_root=None,
        config_action="diff",
    )
    result = cmd_config(args)
    captured = capsys.readouterr().out

    assert result == 0
    assert "sla_p0_hours" in captured
    assert "default=1" in captured
    assert "current=2" in captured
