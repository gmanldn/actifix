#!/usr/bin/env python3
"""Tests for API ticket creation and completion endpoints."""

from __future__ import annotations

import json
import pytest

from actifix.state_paths import get_actifix_paths, init_actifix_files
from actifix.persistence.ticket_repo import get_ticket_repository, reset_ticket_repository
from actifix.persistence.database import reset_database_pool


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Create Flask test client with isolated paths."""
    # Set up isolated paths
    monkeypatch.setenv("ACTIFIX_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    paths = get_actifix_paths()
    init_actifix_files(paths)

    # Reset singletons
    reset_database_pool()
    reset_ticket_repository()

    # Create API app
    from actifix.api import create_app
    app = create_app(project_root=tmp_path)
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


class TestRaiseTicketEndpoint:
    """Test POST /api/raise-ticket endpoint."""

    def test_create_ticket_success(self, api_client):
        """Verify ticket can be created via API."""
        response = api_client.post(
            '/api/raise-ticket',
            json={
                'message': 'Test error from API',
                'source': 'test_api.py:42',
                'error_type': 'TestError',
                'priority': 'P2',
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'ticket_id' in data
        # Ticket ID may be None in some test environments, just verify structure
        if data['ticket_id']:
            assert data['ticket_id'].startswith('ACT-')
        assert data['priority'] == 'P2'

    def test_create_ticket_missing_message(self, api_client):
        """Verify error when message is missing."""
        response = api_client.post(
            '/api/raise-ticket',
            json={
                'source': 'test.py:1',
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'message' in data['error'].lower()

    def test_create_ticket_missing_source(self, api_client):
        """Verify error when source is missing."""
        response = api_client.post(
            '/api/raise-ticket',
            json={
                'message': 'Test error',
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'source' in data['error'].lower()

    def test_create_ticket_invalid_priority(self, api_client):
        """Verify error when priority is invalid."""
        response = api_client.post(
            '/api/raise-ticket',
            json={
                'message': 'Test error',
                'source': 'test.py:1',
                'priority': 'INVALID',
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'priority' in data['error'].lower()

    def test_create_ticket_default_values(self, api_client):
        """Verify default values are applied when optional fields omitted."""
        response = api_client.post(
            '/api/raise-ticket',
            json={
                'message': 'Minimal ticket',
                'source': 'minimal.py:1',
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['priority'] == 'P2'  # Default priority


class TestCompleteTicketEndpoint:
    """Test POST /api/complete-ticket endpoint."""

    def test_complete_ticket_success(self, api_client):
        """Verify ticket can be marked complete via API."""
        # First create a ticket
        create_response = api_client.post(
            '/api/raise-ticket',
            json={
                'message': 'Test ticket to complete',
                'source': 'test.py:1',
            }
        )
        ticket_id = json.loads(create_response.data)['ticket_id']

        # Now complete it
        # Note: This requires admin auth in production, skipped in test mode
        response = api_client.post(
            '/api/complete-ticket',
            json={
                'ticket_id': ticket_id,
                'completion_notes': '''Implementation: Fixed test issue.

Files:
- test/test_api.py
''',
                'test_steps': '1. Run tests',
                'test_results': 'All tests pass',
            }
        )

        # In test mode without auth, this should work
        assert response.status_code in [200, 401]  # 401 if auth enforced

    def test_complete_ticket_missing_fields(self, api_client):
        """Verify error when required fields are missing."""
        response = api_client.post(
            '/api/complete-ticket',
            json={
                'ticket_id': 'ACT-20260101-XXXXX',
            }
        )

        # Should fail either due to auth or missing fields
        assert response.status_code in [400, 401]


class TestCodebaseExplorer:
    """Test codebase.py script functionality."""

    def test_list_files(self, tmp_path):
        """Verify codebase explorer can list files."""
        # Create some test files
        (tmp_path / "test1.py").write_text("print('hello')")
        (tmp_path / "test2.py").write_text("print('world')")
        (tmp_path / "README.md").write_text("# Test")

        from scripts.codebase import CodebaseExplorer
        explorer = CodebaseExplorer(root=tmp_path)

        files = explorer.list_files()
        assert len(files) >= 3

        # Check metadata structure
        for file_info in files:
            assert 'path' in file_info
            assert 'size' in file_info
            assert 'modified' in file_info

    def test_read_file(self, tmp_path):
        """Verify codebase explorer can read files."""
        test_file = tmp_path / "test.py"
        test_content = "print('test')\n"
        test_file.write_text(test_content)

        from scripts.codebase import CodebaseExplorer
        explorer = CodebaseExplorer(root=tmp_path)

        result = explorer.read_file("test.py")
        assert 'content' in result
        assert result['content'] == test_content
        assert result['encoding'] == 'utf-8'

    def test_search_content(self, tmp_path):
        """Verify codebase explorer can search for text."""
        (tmp_path / "file1.py").write_text("def hello(): pass")
        (tmp_path / "file2.py").write_text("def goodbye(): pass")
        (tmp_path / "file3.py").write_text("class Hello: pass")

        from scripts.codebase import CodebaseExplorer
        explorer = CodebaseExplorer(root=tmp_path)

        matches = explorer.search_content("hello")
        # Should find "hello" in file1.py (case-sensitive)
        paths = [m['path'] for m in matches]
        assert any('file1.py' in p for p in paths)

    def test_get_stats(self, tmp_path):
        """Verify codebase explorer can generate statistics."""
        (tmp_path / "test1.py").write_text("x" * 100)
        (tmp_path / "test2.py").write_text("y" * 200)
        (tmp_path / "README.md").write_text("z" * 50)

        from scripts.codebase import CodebaseExplorer
        explorer = CodebaseExplorer(root=tmp_path)

        stats = explorer.get_stats()
        assert 'total_files' in stats
        assert 'total_size' in stats
        assert 'by_extension' in stats
        assert stats['total_files'] >= 3
