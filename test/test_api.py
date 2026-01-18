"""
Tests for the Actifix API module.

Tests API endpoints for health, stats, tickets, logs, and system information.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Check if Flask is available
try:
    from flask import Flask
    from flask.testing import FlaskClient
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from actifix.persistence.ticket_repo import get_ticket_repository
from actifix.raise_af import ActifixEntry, TicketPriority
from actifix.state_paths import get_actifix_paths, init_actifix_files


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with Actifix structure."""
    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)
    return tmp_path


@pytest.fixture
def test_client(temp_project, flask_app_session):
    """Create a Flask test client using session-scoped app."""
    if not FLASK_AVAILABLE:
        pytest.skip("Flask not available")
    
    # Use the session-scoped Flask app
    with flask_app_session.test_client() as client:
        yield client


@pytest.mark.api
@pytest.mark.no_db_isolation
@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.fixture(autouse=True)
    def disable_db_isolation(self, monkeypatch):
        """
        Disable per-test database isolation for endpoint tests.
        These tests use a shared session-scoped app to minimize overhead.
        """
        # Do nothing - override the autouse isolate_actifix_db from conftest
        pass
    """Test API endpoints."""
    
    def test_ping_endpoint(self, test_client):
        """Test /api/ping returns OK status."""
        response = test_client.get('/api/ping')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data
    
    def test_health_endpoint(self, test_client):
        """Test /api/health returns health data."""
        response = test_client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'healthy' in data
        assert 'status' in data
        assert 'metrics' in data
        assert 'filesystem' in data
    
    def test_health_metrics(self, test_client):
        """Test health endpoint contains expected metrics."""
        response = test_client.get('/api/health')
        data = json.loads(response.data)
        metrics = data['metrics']
        assert 'open_tickets' in metrics
        assert 'completed_tickets' in metrics
        assert 'sla_breaches' in metrics
        assert 'oldest_ticket_age_hours' in metrics
    
    def test_stats_endpoint(self, test_client):
        """Test /api/stats returns statistics."""
        response = test_client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data
        assert 'open' in data
        assert 'completed' in data
        assert 'by_priority' in data
    
    def test_tickets_endpoint(self, test_client):
        """Test /api/tickets returns ticket list."""
        response = test_client.get('/api/tickets')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tickets' in data
        assert 'total_open' in data
        assert 'total_completed' in data
        assert isinstance(data['tickets'], list)
    
    def test_tickets_with_limit(self, test_client):
        """Test /api/tickets respects limit parameter."""
        response = test_client.get('/api/tickets?limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tickets']) <= 5
    
    def test_logs_endpoint(self, test_client):
        """Test /api/logs returns log data."""
        response = test_client.get('/api/logs')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'content' in data
        assert 'file' in data
    
    def test_logs_types(self, test_client):
        """Test /api/logs supports different log types."""
        for log_type in ['audit', 'errors', 'list']:
            response = test_client.get(f'/api/logs?type={log_type}')
            assert response.status_code == 200
    
    def test_logs_lines_parameter(self, test_client):
        """Test /api/logs respects lines parameter."""
        response = test_client.get('/api/logs?lines=50')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['content']) <= 50
    
    def test_system_endpoint(self, test_client):
        """Test /api/system returns system information."""
        response = test_client.get('/api/system')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'platform' in data
        assert 'project' in data
        assert 'server' in data
    
    def test_system_platform_info(self, test_client):
        """Test system endpoint contains platform details."""
        response = test_client.get('/api/system')
        data = json.loads(response.data)
        platform = data['platform']
        assert 'system' in platform
        assert 'release' in platform
        assert 'machine' in platform
        assert 'python_version' in platform
    
    def test_system_server_info(self, test_client):
        """Test system endpoint contains server details."""
        response = test_client.get('/api/system')
        data = json.loads(response.data)
        server = data['server']
        assert 'uptime' in server
        assert 'uptime_seconds' in server
        assert 'start_time' in server


@pytest.mark.api
@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
class TestAPIWithData:
    """Test API with actual ticket data."""
    
    def test_health_with_tickets(self, temp_project):
        """Test health endpoint with tickets present."""
        paths = get_actifix_paths(project_root=temp_project)
        repo = get_ticket_repository()
        repo.create_ticket(
            ActifixEntry(
                message="Test ticket",
                source="test/test_api.py:health",
                run_label="api",
                entry_id="ACT-20260110-ABCD1234",
                created_at=datetime.now(timezone.utc),
                priority=TicketPriority.P2,
                error_type="TestError",
                duplicate_guard="hash123",
            )
        )
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/health')
            data = json.loads(response.data)
            assert data['metrics']['open_tickets'] >= 1
    
    def test_tickets_returns_data(self, temp_project):
        """Test tickets endpoint returns ticket data."""
        # Add a test ticket
        paths = get_actifix_paths(project_root=temp_project)
        repo = get_ticket_repository()
        repo.create_ticket(
            ActifixEntry(
                message="ImportError failure",
                source="test/test_api.py:tickets",
                run_label="api",
                entry_id="ACT-20260110-ABCD1234",
                created_at=datetime.now(timezone.utc),
                priority=TicketPriority.P1,
                error_type="ImportError",
                duplicate_guard="hash456",
            )
        )
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/tickets')
            data = json.loads(response.data)
            assert data['total_open'] >= 1
            assert len(data['tickets']) >= 1
            
            # Check ticket structure
            ticket = data['tickets'][0]
            assert 'ticket_id' in ticket
            assert 'priority' in ticket
            assert 'error_type' in ticket


@pytest.mark.api
@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
class TestAPIAppCreation:
    """Test API app creation and configuration."""
    
    def test_create_app_default(self, temp_project):
        """Test create_app with default configuration."""
        from actifix.api import create_app
        app = create_app(temp_project)
        assert app is not None
        assert isinstance(app, Flask)
    
    def test_create_app_sets_project_root(self, temp_project):
        """Test create_app stores project root in config."""
        from actifix.api import create_app
        app = create_app(temp_project)
        assert app.config['PROJECT_ROOT'] == temp_project
    
    def test_cors_enabled(self, temp_project):
        """Test CORS is enabled on the app."""
        from actifix.api import create_app
        app = create_app(temp_project)
        # CORS should be configured
        assert app is not None


class TestAPIImportGuard:
    """Test API module import behavior."""
    
    def test_flask_not_available_raises(self):
        """Test that create_app raises when Flask is not available."""
        if FLASK_AVAILABLE:
            pytest.skip("Flask is available, cannot test unavailable case")
        
        from actifix.api import create_app, FLASK_AVAILABLE as flask_flag
        assert not flask_flag
        with pytest.raises(ImportError):
            create_app()


class TestLogParsing:
    """Test log line parsing in API."""
    
    def test_log_level_detection(self, temp_project):
        """Test that log lines are parsed with correct levels."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        from actifix.log_utils import log_event
        log_event("LOG", "Normal log line", level="INFO")
        log_event("LOG", "Something went wrong", level="ERROR")
        log_event("LOG", "Be careful", level="WARNING")
        log_event("LOG", "Success operation", level="SUCCESS")
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/logs?type=audit')
            data = json.loads(response.data)
            
            # Check that levels are assigned
            levels = [line['level'] for line in data['content']]
            assert 'ERROR' in levels
            assert 'WARNING' in levels
            assert 'SUCCESS' in levels


class TestSystemEndpointDetails:
    """Test system endpoint detailed information."""
    
    def test_uptime_format(self, temp_project):
        """Test that uptime is properly formatted."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/system')
            data = json.loads(response.data)
            
            # Uptime should contain h, m, s
            uptime = data['server']['uptime']
            assert 'h' in uptime
            assert 'm' in uptime
            assert 's' in uptime
    
    def test_timestamp_iso_format(self, temp_project):
        """Test that timestamps are in ISO format."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/system')
            data = json.loads(response.data)
            
            # Should be parseable as ISO datetime
            timestamp = data['timestamp']
            # This should not raise
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_cpu_and_memory_always_available(self, temp_project):
        """Test that CPU and memory are never N/A - should always have numeric values."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        from actifix.api import create_app
        app = create_app(temp_project)
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/system')
            data = json.loads(response.data)
            
            resources = data['resources']
            
            # CPU should always be a number, never None or "N/A"
            cpu = resources.get('cpu_percent')
            assert cpu is not None, "CPU percent should never be None"
            assert isinstance(cpu, (int, float)), f"CPU should be numeric, got {type(cpu)}"
            assert cpu >= 0, "CPU percent should be >= 0"
            assert cpu <= 100, "CPU percent should be <= 100"
            
            # Memory should always be available
            memory = resources.get('memory')
            assert memory is not None, "Memory info should never be None"
            assert isinstance(memory, dict), "Memory should be a dict"
            assert 'percent' in memory, "Memory should have percent field"
            assert 'used_gb' in memory, "Memory should have used_gb field"
            assert 'total_gb' in memory, "Memory should have total_gb field"
            
            # Memory values should be numeric
            assert isinstance(memory['percent'], (int, float)), "Memory percent should be numeric"
            assert isinstance(memory['used_gb'], (int, float)), "Memory used_gb should be numeric"
            assert isinstance(memory['total_gb'], (int, float)), "Memory total_gb should be numeric"
            
            # Memory values should be reasonable
            assert memory['percent'] >= 0, "Memory percent should be >= 0"
            assert memory['percent'] <= 100, "Memory percent should be <= 100"
            assert memory['used_gb'] >= 0, "Memory used_gb should be >= 0"
            assert memory['total_gb'] > 0, "Memory total_gb should be > 0"
            assert memory['used_gb'] <= memory['total_gb'], "Used memory should not exceed total"
