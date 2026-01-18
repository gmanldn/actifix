"""
Comprehensive tests for Actifix main entry point.
Tests CLI commands, argument parsing, and application lifecycle.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

from actifix.main import (
    main,
    cmd_init,
    cmd_health,
    cmd_record,
    cmd_process,
    cmd_stats,
    cmd_quarantine,
    cmd_test,
)


class TestMainArgumentParsing:
    """Test argument parsing and CLI structure."""
    
    def test_main_no_args_shows_help(self, capsys):
        """Test that running with no args shows help."""
        result = main([])
        captured = capsys.readouterr()
        assert result == 1
        assert "usage:" in captured.out.lower()
    
    def test_main_help_flag(self, capsys):
        """Test --help flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "actifix" in captured.out.lower()
    
    def test_main_project_root_argument(self, tmp_path):
        """Test --project-root argument parsing."""
        with patch('actifix.main.cmd_init') as mock_cmd:
            mock_cmd.return_value = 0
            main(["--project-root", str(tmp_path), "init"])
            
            args = mock_cmd.call_args[0][0]
            assert args.project_root == str(tmp_path)
    
    def test_main_invalid_command(self, capsys):
        """Test invalid command."""
        with pytest.raises(SystemExit):
            main(["invalid_command"])


class TestCmdInit:
    """Test 'init' command."""
    
    def test_cmd_init_default_directory(self, tmp_path, monkeypatch, capsys):
        """Test init in current directory."""
        monkeypatch.chdir(tmp_path)
        
        args = argparse.Namespace(project_root=None)
        result = cmd_init(args)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "initialized successfully" in captured.out.lower()
        assert (tmp_path / ".actifix").exists()
    
    def test_cmd_init_custom_directory(self, tmp_path, capsys):
        """Test init in custom directory."""
        custom_dir = tmp_path / "custom_project"
        custom_dir.mkdir()
        
        args = argparse.Namespace(project_root=str(custom_dir))
        result = cmd_init(args)
        
        assert result == 0
        assert (custom_dir / ".actifix").exists()
    
    def test_cmd_init_creates_all_files(self, tmp_path, capsys):
        """Test init creates all required files."""
        args = argparse.Namespace(project_root=str(tmp_path))
        result = cmd_init(args)
        
        assert result == 0
        actifix_dir = tmp_path / "actifix"
        logs_dir = tmp_path / "logs"
        state_dir = tmp_path / ".actifix"
        assert actifix_dir.exists()
        assert logs_dir.exists()
        assert (logs_dir / "actifix.log").exists()
        assert (state_dir / "actifix_fallback_queue.json").exists()
        assert (state_dir / "RAISE_AF_ONLY").exists()


class TestCmdHealth:
    """Test 'health' command."""
    
    def test_cmd_health_healthy_system(self, tmp_path):
        """Test health check with healthy system."""
        with patch('actifix.main.run_health_check') as mock_health:
            mock_health.return_value = MagicMock(healthy=True)
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_health(args)
            
            assert result == 0
            mock_health.assert_called_once_with(print_report=True)
    
    def test_cmd_health_unhealthy_system(self, tmp_path):
        """Test health check with unhealthy system."""
        with patch('actifix.main.run_health_check') as mock_health:
            mock_health.return_value = MagicMock(healthy=False)
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_health(args)
            
            assert result == 1


class TestCmdRecord:
    """Test 'record' command."""
    
    def test_cmd_record_success(self, tmp_path, capsys):
        """Test recording an error successfully."""
        with patch('actifix.main.record_error') as mock_record:
            mock_entry = MagicMock(ticket_id="ACT-001")
            mock_record.return_value = mock_entry
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                error_type="TestError",
                message="Test message",
                source="test/test_runner.py:10",
                priority="P2",
            )
            
            result = cmd_record(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "ACT-001" in captured.out
    
    def test_cmd_record_duplicate(self, tmp_path, capsys):
        """Test recording a duplicate error."""
        with patch('actifix.main.record_error') as mock_record:
            mock_record.return_value = None
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                error_type="TestError",
                message="Test message",
                source="test/test_runner.py:10",
                priority="P2",
            )
            
            result = cmd_record(args)
            
            assert result == 1
            captured = capsys.readouterr()
            assert "not created" in captured.out.lower()
    
    def test_cmd_record_all_priorities(self, tmp_path):
        """Test recording with all priority levels."""
        for priority in ["P0", "P1", "P2", "P3"]:
            with patch('actifix.main.record_error') as mock_record:
                mock_entry = MagicMock(ticket_id=f"ACT-{priority}")
                mock_record.return_value = mock_entry
                
                args = argparse.Namespace(
                    project_root=str(tmp_path),
                    error_type="TestError",
                    message="Test",
                    source="test/test_runner.py:1",
                    priority=priority,
                )
                
                result = cmd_record(args)
                assert result == 0


class TestCmdProcess:
    """Test 'process' command."""
    
    def test_cmd_process_no_tickets(self, tmp_path, capsys):
        """Test processing when no tickets exist."""
        with patch('actifix.main.process_tickets') as mock_process:
            mock_process.return_value = []
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                max_tickets=5,
            )
            
            result = cmd_process(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "no tickets" in captured.out.lower()
    
    def test_cmd_process_multiple_tickets(self, tmp_path, capsys):
        """Test processing multiple tickets."""
        with patch('actifix.main.process_tickets') as mock_process:
            tickets = [
                MagicMock(ticket_id="ACT-001", error_type="Error1"),
                MagicMock(ticket_id="ACT-002", error_type="Error2"),
            ]
            mock_process.return_value = tickets
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                max_tickets=5,
            )
            
            result = cmd_process(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "processed 2 ticket" in captured.out.lower()
            assert "ACT-001" in captured.out
            assert "ACT-002" in captured.out
    
    def test_cmd_process_respects_max_tickets(self, tmp_path):
        """Test that max_tickets parameter is passed."""
        with patch('actifix.main.process_tickets') as mock_process:
            mock_process.return_value = []
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                max_tickets=10,
            )
            
            cmd_process(args)
            
            mock_process.assert_called_once_with(max_tickets=10)


class TestCmdStats:
    """Test 'stats' command."""
    
    def test_cmd_stats_empty(self, tmp_path, capsys):
        """Test stats with no tickets."""
        with patch('actifix.main.get_ticket_stats') as mock_stats:
            mock_stats.return_value = {
                'total': 0,
                'open': 0,
                'completed': 0,
                'by_priority': {},
            }
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_stats(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "total tickets: 0" in captured.out.lower()
    
    def test_cmd_stats_with_data(self, tmp_path, capsys):
        """Test stats with ticket data."""
        with patch('actifix.main.get_ticket_stats') as mock_stats:
            mock_stats.return_value = {
                'total': 10,
                'open': 3,
                'completed': 7,
                'by_priority': {
                    'P0': 1,
                    'P1': 2,
                    'P2': 5,
                    'P3': 2,
                },
            }
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_stats(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "total tickets: 10" in captured.out.lower()
            assert "open: 3" in captured.out.lower()
            assert "completed: 7" in captured.out.lower()
            assert "P0: 1" in captured.out
            assert "P2: 5" in captured.out


class TestCmdQuarantine:
    """Test 'quarantine' command."""
    
    def test_cmd_quarantine_list_empty(self, tmp_path, capsys):
        """Test listing empty quarantine."""
        with patch('actifix.main.list_quarantine') as mock_list:
            mock_list.return_value = []
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                quarantine_action="list",
            )
            
            result = cmd_quarantine(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "no quarantined items" in captured.out.lower()
    
    def test_cmd_quarantine_list_with_entries(self, tmp_path, capsys):
        """Test listing quarantine with entries."""
        from datetime import datetime, timezone
        
        with patch('actifix.main.list_quarantine') as mock_list:
            entries = [
                MagicMock(
                    entry_id="quarantine_001",
                    original_source="database",
                    reason="Malformed ticket",
                    quarantined_at=datetime.now(timezone.utc),
                ),
            ]
            mock_list.return_value = entries
            
            args = argparse.Namespace(
                project_root=str(tmp_path),
                quarantine_action="list",
            )
            
            result = cmd_quarantine(args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "quarantine_001" in captured.out
            assert "database" in captured.out
            assert "Malformed ticket" in captured.out


class TestCmdTest:
    """Test 'test' command."""
    
    def test_cmd_test_success(self, tmp_path):
        """Test self-test command success."""
        with patch('actifix.testing.run_tests') as mock_run:
            mock_run.return_value = MagicMock(success=True)
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_test(args)
            
            assert result == 0
    
    def test_cmd_test_failure(self, tmp_path):
        """Test self-test command failure."""
        with patch('actifix.testing.run_tests') as mock_run:
            mock_run.return_value = MagicMock(success=False)
            
            args = argparse.Namespace(project_root=str(tmp_path))
            result = cmd_test(args)
            
            assert result == 1


class TestMainIntegration:
    """Integration tests for main function."""
    
    def test_main_keyboard_interrupt(self, tmp_path, capsys):
        """Test handling of KeyboardInterrupt."""
        with patch('actifix.main.cmd_init') as mock_cmd:
            mock_cmd.side_effect = KeyboardInterrupt()
            
            result = main(["init"])
            
            assert result == 130
            captured = capsys.readouterr()
            assert "interrupted" in captured.out.lower()
    
    def test_main_exception_handling(self, tmp_path, capsys):
        """Test handling of general exceptions."""
        with patch('actifix.main.cmd_init') as mock_cmd:
            mock_cmd.side_effect = ValueError("Test error")
            
            result = main(["init"])
            
            assert result == 1
            captured = capsys.readouterr()
            assert "error:" in captured.err.lower()
    
    def test_main_calls_correct_command(self, tmp_path):
        """Test that main dispatches to correct command."""
        commands = [
            ("init", "cmd_init"),
            ("health", "cmd_health"),
            ("record", "cmd_record"),
            ("process", "cmd_process"),
            ("stats", "cmd_stats"),
            ("quarantine", "cmd_quarantine"),
            ("test", "cmd_test"),
        ]
        
        for cmd_name, func_name in commands:
            with patch(f'actifix.main.{func_name}') as mock_cmd:
                mock_cmd.return_value = 0
                
                if cmd_name == "record":
                    args = [cmd_name, "Error", "msg", "file:1"]
                elif cmd_name == "quarantine":
                    args = [cmd_name, "list"]
                else:
                    args = [cmd_name]
                
                result = main(args)
                
                assert result == 0
                assert mock_cmd.called


class TestMainEdgeCases:
    """Edge case tests for main module."""
    
    def test_main_with_none_argv(self):
        """Test main with None argv (uses sys.argv)."""
        with patch('sys.argv', ['actifix', '--help']):
            with pytest.raises(SystemExit):
                main(None)
    
    def test_cmd_init_nonexistent_directory(self, tmp_path):
        """Test init with non-existent directory creates it."""
        nonexistent = tmp_path / "does_not_exist"
        
        args = argparse.Namespace(project_root=str(nonexistent))
        result = cmd_init(args)
        
        assert result == 0
        assert nonexistent.exists()
    
    def test_multiple_commands_in_sequence(self, tmp_path):
        """Test running multiple commands in sequence."""
        # Init
        with patch('actifix.main.cmd_init') as mock_init:
            mock_init.return_value = 0
            assert main(["init"]) == 0
        
        # Health
        with patch('actifix.main.cmd_health') as mock_health:
            mock_health.return_value = 0
            assert main(["health"]) == 0
        
        # Stats
        with patch('actifix.main.cmd_stats') as mock_stats:
            mock_stats.return_value = 0
            assert main(["stats"]) == 0
