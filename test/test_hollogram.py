# -*- coding: utf-8 -*-

"""Tests for the Hollogram medical research assistant module."""

import importlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def test_module_import():
    """Test that the hollogram module can be imported."""
    mod = importlib.import_module("actifix.modules.hollogram")
    assert hasattr(mod, "MODULE_DEFAULTS")
    assert hasattr(mod, "MODULE_METADATA")
    assert hasattr(mod, "MODULE_DEPENDENCIES")
    assert hasattr(mod, "create_blueprint")


def test_module_metadata_valid():
    """Test that module metadata contains required fields."""
    from actifix.modules.hollogram import MODULE_METADATA

    required_fields = {"name", "version", "description", "capabilities", "data_access", "network", "permissions"}
    assert required_fields.issubset(set(MODULE_METADATA.keys()))
    assert MODULE_METADATA["name"] == "modules.hollogram"
    assert isinstance(MODULE_METADATA["version"], str)
    assert MODULE_METADATA["capabilities"].get("ai") is True
    assert MODULE_METADATA["capabilities"].get("health") is True
    assert MODULE_METADATA["capabilities"].get("research") is True


def test_module_defaults():
    """Test that module defaults are properly defined."""
    from actifix.modules.hollogram import MODULE_DEFAULTS

    assert "host" in MODULE_DEFAULTS
    assert "port" in MODULE_DEFAULTS
    assert "max_query_length" in MODULE_DEFAULTS
    assert "history_limit" in MODULE_DEFAULTS
    assert MODULE_DEFAULTS["max_query_length"] > 0
    assert MODULE_DEFAULTS["history_limit"] > 0


def test_module_dependencies():
    """Test that module dependencies are properly defined."""
    from actifix.modules.hollogram import MODULE_DEPENDENCIES

    assert isinstance(MODULE_DEPENDENCIES, list)
    assert "runtime.state" in MODULE_DEPENDENCIES
    assert "infra.logging" in MODULE_DEPENDENCIES
    assert "core.raise_af" in MODULE_DEPENDENCIES
    assert "runtime.api" in MODULE_DEPENDENCIES
    assert "core.ai_client" in MODULE_DEPENDENCIES


def test_blueprint_creation():
    """Test that the blueprint can be created."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    blueprint = create_blueprint()
    assert blueprint.name == "hollogram"


def test_gui_blueprint_creation():
    """Test that the GUI blueprint can be created."""
    from actifix.modules.hollogram import create_gui_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping GUI blueprint test")

    app = Flask(__name__)
    blueprint = create_gui_blueprint()
    app.register_blueprint(blueprint)
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Hollogram Research Console" in resp.get_data(as_text=True)


def test_health_endpoint():
    """Test the /health endpoint."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.get("/modules/hollogram/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("status") == "ok"
        assert data.get("module") == "hollogram"


def test_disclaimer_endpoint():
    """Test the /disclaimer endpoint."""
    from actifix.modules.hollogram import create_blueprint, MEDICAL_DISCLAIMER

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.get("/modules/hollogram/disclaimer")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "disclaimer" in data
        assert "educational" in data["disclaimer"].lower() or "EDUCATIONAL" in data["disclaimer"]
        assert "version" in data


def test_topics_endpoint():
    """Test the /topics endpoint."""
    from actifix.modules.hollogram import create_blueprint, TOPIC_CATEGORIES

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.get("/modules/hollogram/topics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "topics" in data
        assert "count" in data
        assert data["count"] == len(TOPIC_CATEGORIES)

        topic_ids = [t["id"] for t in data["topics"]]
        assert "anatomy" in topic_ids
        assert "conditions" in topic_ids
        assert "medications" in topic_ids


def test_research_missing_query():
    """Test that /research returns 400 for missing query."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.post("/modules/hollogram/research", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data


def test_research_disclaimer_not_accepted():
    """Test that /research returns 400 when disclaimer not accepted."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.post(
            "/modules/hollogram/research",
            json={"query": "What is diabetes?", "disclaimer_accepted": False},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "disclaimer" in data.get("error", "").lower()


def test_research_query_too_long():
    """Test that /research returns 400 for queries exceeding max length."""
    from actifix.modules.hollogram import create_blueprint, MODULE_DEFAULTS

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    max_length = MODULE_DEFAULTS["max_query_length"]
    long_query = "x" * (max_length + 100)

    with app.test_client() as client:
        resp = client.post(
            "/modules/hollogram/research",
            json={"query": long_query, "disclaimer_accepted": True},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "exceeds" in data.get("error", "").lower() or "length" in data.get("error", "").lower()


def test_research_invalid_category():
    """Test that /research returns 400 for invalid category."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.post(
            "/modules/hollogram/research",
            json={
                "query": "What is diabetes?",
                "category": "invalid_category",
                "disclaimer_accepted": True,
            },
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "invalid" in data.get("error", "").lower() or "category" in data.get("error", "").lower()


def test_urgent_query_detection():
    """Test that urgent medical queries are detected and handled appropriately."""
    from actifix.modules.hollogram import _detect_urgent_query

    # These should be detected as urgent
    assert _detect_urgent_query("I'm having chest pain and can't breathe") is True
    assert _detect_urgent_query("I think I'm having a heart attack") is True
    assert _detect_urgent_query("Should I call 911?") is True
    assert _detect_urgent_query("I took too many pills, is this an overdose?") is True

    # These should NOT be detected as urgent
    assert _detect_urgent_query("What is diabetes?") is False
    assert _detect_urgent_query("How does aspirin work?") is False
    assert _detect_urgent_query("What are the symptoms of the common cold?") is False


def test_urgent_query_response():
    """Test that urgent queries return appropriate emergency information."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    app = Flask(__name__)
    blueprint = create_blueprint()
    app.register_blueprint(blueprint)

    with app.test_client() as client:
        resp = client.post(
            "/modules/hollogram/research",
            json={
                "query": "I'm having severe chest pain, should I call 911?",
                "disclaimer_accepted": True,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("urgent") is True
        assert "resources" in data
        assert "emergency" in data["resources"]


def test_citation_extraction():
    """Test citation extraction from AI responses."""
    from actifix.modules.hollogram import _extract_citations

    response1 = "Diabetes is a condition [Source: CDC Guidelines 2024]. Treatment includes [Citation: ADA Standards]."
    citations1 = _extract_citations(response1)
    assert "CDC Guidelines 2024" in citations1
    assert "ADA Standards" in citations1

    response2 = "According to studies [1] and [2], this treatment is effective."
    citations2 = _extract_citations(response2)
    assert "Reference 1" in citations2
    assert "Reference 2" in citations2


def test_research_with_mocked_ai():
    """Test /research endpoint with mocked AI client."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    # Create a mock AI response
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.content = "Diabetes is a chronic condition [Source: Medical Encyclopedia]. Please consult a doctor."
    mock_response.provider = MagicMock()
    mock_response.provider.value = "mock_provider"

    mock_client = MagicMock()
    mock_client.generate_fix.return_value = mock_response

    # Patch at the source module where get_ai_client is defined
    with patch("actifix.ai_client.get_ai_client", return_value=mock_client):
        app = Flask(__name__)
        blueprint = create_blueprint()
        app.register_blueprint(blueprint)

        with app.test_client() as client:
            resp = client.post(
                "/modules/hollogram/research",
                json={
                    "query": "What is diabetes?",
                    "category": "conditions",
                    "disclaimer_accepted": True,
                },
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data.get("success") is True
            assert "diabetes" in data.get("response", "").lower()
            assert data.get("provider") == "mock_provider"
            assert "citations" in data
            assert data.get("category") == "conditions"


def test_history_endpoints_empty():
    """Test history endpoints when no history exists."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    with tempfile.TemporaryDirectory() as tmpdir:
        app = Flask(__name__)
        blueprint = create_blueprint(project_root=Path(tmpdir))
        app.register_blueprint(blueprint)

        with app.test_client() as client:
            resp = client.get("/modules/hollogram/history")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data.get("success") is True
            assert data.get("history") == []
            assert data.get("count") == 0


def test_history_entry_not_found():
    """Test that accessing non-existent history entry returns 404."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    with tempfile.TemporaryDirectory() as tmpdir:
        app = Flask(__name__)
        blueprint = create_blueprint(project_root=Path(tmpdir))
        app.register_blueprint(blueprint)

        with app.test_client() as client:
            resp = client.get("/modules/hollogram/history/99999")
            assert resp.status_code == 404


def test_delete_history_entry_not_found():
    """Test that deleting non-existent history entry returns 404."""
    from actifix.modules.hollogram import create_blueprint

    try:
        from flask import Flask
    except ImportError:
        pytest.skip("Flask not installed; skipping blueprint test")

    with tempfile.TemporaryDirectory() as tmpdir:
        app = Flask(__name__)
        blueprint = create_blueprint(project_root=Path(tmpdir))
        app.register_blueprint(blueprint)

        with app.test_client() as client:
            resp = client.delete("/modules/hollogram/history/99999")
            assert resp.status_code == 404


def test_history_save_and_retrieve():
    """Test that history entries are saved and can be retrieved."""
    from actifix.modules.hollogram import (
        _init_database,
        _save_history_entry,
        _get_history,
        _get_history_entry,
        _delete_history_entry,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        _init_database(db_path)

        # Save an entry
        entry_id = _save_history_entry(
            db_path,
            query="What is diabetes?",
            category="conditions",
            response="Diabetes is a chronic condition affecting blood sugar.",
            provider="test_provider",
            citations=["CDC", "ADA"],
            history_limit=100,
        )

        assert entry_id is not None
        assert entry_id > 0

        # Retrieve history
        history = _get_history(db_path, limit=10)
        assert len(history) == 1
        assert history[0]["query"] == "What is diabetes?"
        assert history[0]["category"] == "conditions"
        assert "test_provider" == history[0]["provider"]

        # Retrieve single entry
        entry = _get_history_entry(db_path, entry_id)
        assert entry is not None
        assert entry["query"] == "What is diabetes?"
        assert "CDC" in entry["citations"]
        assert "ADA" in entry["citations"]

        # Delete entry
        deleted = _delete_history_entry(db_path, entry_id)
        assert deleted is True

        # Verify deletion
        entry = _get_history_entry(db_path, entry_id)
        assert entry is None


def test_history_limit_enforcement():
    """Test that history limit is enforced."""
    from actifix.modules.hollogram import (
        _init_database,
        _save_history_entry,
        _get_history,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        _init_database(db_path)

        history_limit = 5

        # Save more entries than the limit
        for i in range(10):
            _save_history_entry(
                db_path,
                query=f"Query {i}",
                category="conditions",
                response=f"Response {i}",
                provider="test",
                citations=[],
                history_limit=history_limit,
            )

        # Check that only the limit number of entries exist
        history = _get_history(db_path, limit=100)
        assert len(history) == history_limit


def test_medical_disclaimer_content():
    """Test that the medical disclaimer contains required elements."""
    from actifix.modules.hollogram import MEDICAL_DISCLAIMER

    disclaimer_lower = MEDICAL_DISCLAIMER.lower()

    # Must mention it's for educational purposes
    assert "educational" in disclaimer_lower or "research" in disclaimer_lower

    # Must disclaim medical advice
    assert "not" in disclaimer_lower and ("medical advice" in disclaimer_lower or "substitute" in disclaimer_lower)

    # Must recommend consulting professionals
    assert "physician" in disclaimer_lower or "healthcare" in disclaimer_lower or "doctor" in disclaimer_lower


def test_topic_categories_structure():
    """Test that topic categories have required structure."""
    from actifix.modules.hollogram import TOPIC_CATEGORIES

    assert isinstance(TOPIC_CATEGORIES, list)
    assert len(TOPIC_CATEGORIES) > 0

    for topic in TOPIC_CATEGORIES:
        assert "id" in topic
        assert "name" in topic
        assert "description" in topic
        assert isinstance(topic["id"], str)
        assert isinstance(topic["name"], str)
        assert isinstance(topic["description"], str)


def test_access_rule_local_only():
    """Test that the module has local-only access rule."""
    from actifix.modules.hollogram import ACCESS_RULE

    assert ACCESS_RULE == "local-only"
