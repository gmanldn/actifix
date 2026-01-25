# -*- coding: utf-8 -*-

"""Regression tests for Hollogram module API contract.

These tests ensure the API contract remains stable and the module
integrates correctly with the Actifix framework.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestHollogramAPIContract:
    """Regression tests for API response structure."""

    @pytest.fixture
    def flask_app(self):
        """Create a Flask app with hollogram blueprint."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.modules.hollogram import create_blueprint

        app = Flask(__name__)
        blueprint = create_blueprint()
        app.register_blueprint(blueprint)
        return app

    def test_health_response_structure(self, flask_app):
        """Ensure health response has required fields."""
        with flask_app.test_client() as client:
            resp = client.get("/modules/hollogram/health")
            assert resp.status_code == 200
            data = resp.get_json()

            # Required fields
            assert "status" in data
            assert "module" in data
            assert data["status"] == "ok"
            assert data["module"] == "hollogram"

    def test_disclaimer_response_structure(self, flask_app):
        """Ensure disclaimer response has required fields."""
        with flask_app.test_client() as client:
            resp = client.get("/modules/hollogram/disclaimer")
            assert resp.status_code == 200
            data = resp.get_json()

            # Required fields
            assert "disclaimer" in data
            assert "version" in data
            assert isinstance(data["disclaimer"], str)
            assert len(data["disclaimer"]) > 100  # Meaningful disclaimer

    def test_topics_response_structure(self, flask_app):
        """Ensure topics response has required fields and format."""
        with flask_app.test_client() as client:
            resp = client.get("/modules/hollogram/topics")
            assert resp.status_code == 200
            data = resp.get_json()

            # Required fields
            assert "topics" in data
            assert "count" in data
            assert isinstance(data["topics"], list)
            assert data["count"] == len(data["topics"])

            # Each topic must have required fields
            for topic in data["topics"]:
                assert "id" in topic
                assert "name" in topic
                assert "description" in topic

    def test_topics_contains_expected_categories(self, flask_app):
        """Ensure all expected topic categories exist."""
        expected_categories = {
            "anatomy",
            "conditions",
            "medications",
            "procedures",
            "terminology",
            "research_methods",
            "clinical_trials",
        }

        with flask_app.test_client() as client:
            resp = client.get("/modules/hollogram/topics")
            data = resp.get_json()
            topic_ids = {t["id"] for t in data["topics"]}

            assert expected_categories == topic_ids

    def test_research_success_response_structure(self, flask_app):
        """Ensure successful research response has required fields."""
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = "Test response [Source: Test]"
        mock_response.provider = MagicMock()
        mock_response.provider.value = "test"

        mock_client = MagicMock()
        mock_client.generate_fix.return_value = mock_response

        with patch("actifix.ai_client.get_ai_client", return_value=mock_client):
            with flask_app.test_client() as client:
                resp = client.post(
                    "/modules/hollogram/research",
                    json={
                        "query": "What is aspirin?",
                        "category": "medications",
                        "disclaimer_accepted": True,
                    },
                )
                assert resp.status_code == 200
                data = resp.get_json()

                # Required fields for success response
                assert "success" in data
                assert "query" in data
                assert "category" in data
                assert "response" in data
                assert "citations" in data
                assert "provider" in data
                assert "disclaimer" in data
                assert "timestamp" in data

                assert data["success"] is True
                assert isinstance(data["citations"], list)

    def test_research_urgent_response_structure(self, flask_app):
        """Ensure urgent query response has required fields."""
        with flask_app.test_client() as client:
            resp = client.post(
                "/modules/hollogram/research",
                json={
                    "query": "I am having a heart attack what do I do",
                    "disclaimer_accepted": True,
                },
            )
            assert resp.status_code == 200
            data = resp.get_json()

            # Required fields for urgent response
            assert "urgent" in data
            assert data["urgent"] is True
            assert "message" in data
            assert "action_required" in data
            assert "resources" in data
            assert "disclaimer" in data

            # Resources must include emergency info
            assert "emergency" in data["resources"]

    def test_research_error_response_structure(self, flask_app):
        """Ensure error responses have required fields."""
        with flask_app.test_client() as client:
            # Missing query
            resp = client.post("/modules/hollogram/research", json={})
            assert resp.status_code == 400
            data = resp.get_json()
            assert "error" in data

            # Disclaimer not accepted
            resp = client.post(
                "/modules/hollogram/research",
                json={"query": "test", "disclaimer_accepted": False},
            )
            assert resp.status_code == 400
            data = resp.get_json()
            assert "error" in data

    def test_history_response_structure(self, flask_app):
        """Ensure history response has required fields."""
        with flask_app.test_client() as client:
            resp = client.get("/modules/hollogram/history")
            assert resp.status_code == 200
            data = resp.get_json()

            # Required fields
            assert "success" in data
            assert "history" in data
            assert "count" in data
            assert "limit" in data

            assert isinstance(data["history"], list)


class TestHollogramModuleIntegration:
    """Tests for module integration with Actifix framework."""

    def test_module_registered_in_api(self):
        """Ensure module is registered when API app is created."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.api import create_app

        with tempfile.TemporaryDirectory() as tmpdir:
            app = create_app(project_root=Path(tmpdir))

            # Check that hollogram routes are registered
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            hollogram_rules = [r for r in rules if "/modules/hollogram" in r]

            assert len(hollogram_rules) > 0, "Hollogram routes not registered"
            assert "/modules/hollogram/health" in rules
            assert "/modules/hollogram/disclaimer" in rules
            assert "/modules/hollogram/topics" in rules
            assert "/modules/hollogram/research" in rules
            assert "/modules/hollogram/history" in rules

    def test_module_appears_in_depgraph(self):
        """Ensure module is in DEPGRAPH.json."""
        depgraph_path = Path(__file__).parent.parent / "docs" / "architecture" / "DEPGRAPH.json"

        if not depgraph_path.exists():
            pytest.skip("DEPGRAPH.json not found")

        data = json.loads(depgraph_path.read_text())

        # Check node exists
        node_ids = [n["id"] for n in data.get("nodes", [])]
        assert "modules.hollogram" in node_ids

        # Check edges exist
        hollogram_edges = [
            e for e in data.get("edges", []) if e.get("from") == "modules.hollogram"
        ]
        assert len(hollogram_edges) > 0

        # Verify expected dependencies
        edge_targets = {e["to"] for e in hollogram_edges}
        expected_deps = {
            "modules.base",
            "modules.config",
            "runtime.state",
            "infra.logging",
            "core.raise_af",
            "runtime.api",
            "core.ai_client",
        }
        assert expected_deps == edge_targets

    def test_module_metadata_matches_schema(self):
        """Ensure module metadata matches framework requirements."""
        from actifix.modules.hollogram import MODULE_METADATA

        required_fields = {
            "name",
            "version",
            "description",
            "capabilities",
            "data_access",
            "network",
            "permissions",
        }

        assert required_fields.issubset(set(MODULE_METADATA.keys()))

        # Name must match module path
        assert MODULE_METADATA["name"] == "modules.hollogram"

        # Version must be semver-like
        version = MODULE_METADATA["version"]
        assert len(version.split(".")) == 3

        # Capabilities must be a dict
        assert isinstance(MODULE_METADATA["capabilities"], dict)

        # Permissions must be a list
        assert isinstance(MODULE_METADATA["permissions"], list)

    def test_module_has_local_only_access(self):
        """Ensure module has local-only access rule for security."""
        from actifix.modules.hollogram import ACCESS_RULE

        assert ACCESS_RULE == "local-only"


class TestHollogramDataPersistence:
    """Tests for history data persistence."""

    def test_history_persists_across_requests(self):
        """Ensure history entries persist across multiple requests."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.modules.hollogram import create_blueprint

        with tempfile.TemporaryDirectory() as tmpdir:
            app = Flask(__name__)
            blueprint = create_blueprint(project_root=Path(tmpdir))
            app.register_blueprint(blueprint)

            mock_response = MagicMock()
            mock_response.success = True
            mock_response.content = "Test response"
            mock_response.provider = MagicMock()
            mock_response.provider.value = "test"

            mock_client = MagicMock()
            mock_client.generate_fix.return_value = mock_response

            with patch("actifix.ai_client.get_ai_client", return_value=mock_client):
                with app.test_client() as client:
                    # Make a research query
                    client.post(
                        "/modules/hollogram/research",
                        json={
                            "query": "Test query 1",
                            "disclaimer_accepted": True,
                        },
                    )

                    # Check history
                    resp = client.get("/modules/hollogram/history")
                    data = resp.get_json()
                    assert data["count"] >= 1

                    # Make another query
                    client.post(
                        "/modules/hollogram/research",
                        json={
                            "query": "Test query 2",
                            "disclaimer_accepted": True,
                        },
                    )

                    # Check history increased
                    resp = client.get("/modules/hollogram/history")
                    data = resp.get_json()
                    assert data["count"] >= 2

    def test_history_delete_works(self):
        """Ensure history entries can be deleted."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.modules.hollogram import (
            create_blueprint,
            _init_database,
            _save_history_entry,
            _get_db_path,
            _module_helper,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            app = Flask(__name__)
            blueprint = create_blueprint(project_root=Path(tmpdir))
            app.register_blueprint(blueprint)

            # Manually create a history entry
            helper = _module_helper(Path(tmpdir))
            db_path = _get_db_path(helper)
            _init_database(db_path)

            entry_id = _save_history_entry(
                db_path,
                query="Test delete",
                category="test",
                response="Response",
                provider="test",
                citations=[],
                history_limit=100,
            )

            with app.test_client() as client:
                # Verify entry exists
                resp = client.get(f"/modules/hollogram/history/{entry_id}")
                assert resp.status_code == 200

                # Delete entry
                resp = client.delete(f"/modules/hollogram/history/{entry_id}")
                assert resp.status_code == 200

                # Verify entry is gone
                resp = client.get(f"/modules/hollogram/history/{entry_id}")
                assert resp.status_code == 404


class TestHollogramSafetyFeatures:
    """Tests for safety features."""

    def test_all_urgent_patterns_detected(self):
        """Ensure all urgent pattern categories are detected."""
        from actifix.modules.hollogram import _detect_urgent_query

        urgent_queries = [
            # Emergency keywords
            "This is an emergency please help",
            "I need urgent medical help",
            "Should I call 911",
            "I need an ambulance",
            # Cardiac/respiratory
            "I have severe chest pain",
            "I think I'm having a heart attack",
            "I'm having a stroke",
            "I can't breathe",
            "I have difficulty breathing",
            # Mental health crisis
            "I want to kill myself",
            "I'm feeling suicidal",
            "I want to end my life",
            # Poisoning/overdose
            "I think I overdosed",
            "I have poisoning symptoms",
            "I'm having a severe allergic reaction",
            # Bleeding
            "I have severe bleeding",
            "The bleeding won't stop",
        ]

        for query in urgent_queries:
            assert _detect_urgent_query(query), f"Should detect as urgent: {query}"

    def test_normal_queries_not_flagged_urgent(self):
        """Ensure normal educational queries are not flagged as urgent."""
        from actifix.modules.hollogram import _detect_urgent_query

        normal_queries = [
            "What is the anatomy of the heart",
            "How does insulin work",
            "What are the stages of clinical trials",
            "Explain the mechanism of aspirin",
            "What is the difference between type 1 and type 2 diabetes",
            "How do vaccines work",
            "What is the role of the liver",
            "Describe the nervous system",
        ]

        for query in normal_queries:
            assert not _detect_urgent_query(query), f"Should not flag as urgent: {query}"

    def test_disclaimer_required_for_research(self):
        """Ensure disclaimer must be accepted for research queries."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.modules.hollogram import create_blueprint

        app = Flask(__name__)
        blueprint = create_blueprint()
        app.register_blueprint(blueprint)

        with app.test_client() as client:
            # Without disclaimer_accepted
            resp = client.post(
                "/modules/hollogram/research",
                json={"query": "What is diabetes?"},
            )
            assert resp.status_code == 400

            # With disclaimer_accepted=False
            resp = client.post(
                "/modules/hollogram/research",
                json={"query": "What is diabetes?", "disclaimer_accepted": False},
            )
            assert resp.status_code == 400

    def test_query_length_limit_enforced(self):
        """Ensure query length limit is enforced."""
        try:
            from flask import Flask
        except ImportError:
            pytest.skip("Flask not installed")

        from actifix.modules.hollogram import create_blueprint, MODULE_DEFAULTS

        app = Flask(__name__)
        blueprint = create_blueprint()
        app.register_blueprint(blueprint)

        max_len = MODULE_DEFAULTS["max_query_length"]

        with app.test_client() as client:
            # Query at limit should work (will fail on AI, but pass validation)
            # Query over limit should fail validation
            resp = client.post(
                "/modules/hollogram/research",
                json={
                    "query": "x" * (max_len + 1),
                    "disclaimer_accepted": True,
                },
            )
            assert resp.status_code == 400
            assert "exceeds" in resp.get_json().get("error", "").lower()
