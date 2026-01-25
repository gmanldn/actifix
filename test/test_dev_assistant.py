# -*- coding: utf-8 -*-

import importlib
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from actifix.config import load_config


def test_config_defaults():
    config = load_config()
    assert config.ai_provider == "", f"Expected ai_provider default to be empty, got {config.ai_provider}"
    assert config.ai_model == 'qwen2.5-coder:7b-instruct', f"Expected ai_model 'qwen2.5-coder:7b-instruct', got {config.ai_model}"
    assert config.ollama_model == 'qwen2.5-coder:7b-instruct', f"Expected ollama_model 'qwen2.5-coder:7b-instruct', got {config.ollama_model}"


def test_module_import_and_blueprint():
    mod = importlib.import_module('actifix.modules.dev_assistant')
    blueprint = mod.create_blueprint()
    assert blueprint.name == 'dev_assistant'
    # Use Flask's test client to verify endpoints
    try:
        from flask import Flask
    except ImportError:
        pytest.skip('Flask not installed; skipping blueprint test')
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    with app.test_client() as client:
        # Health should return 200
        resp = client.get('/modules/dev_assistant/health')
        assert resp.status_code == 200, f"Health returned {resp.status_code}"
        # Missing prompt should return 400
        resp = client.post('/modules/dev_assistant/chat', json={})
        assert resp.status_code == 400, f"Empty prompt should return 400, got {resp.status_code}"


def test_module_registered_in_api():
    try:
        from flask import Flask  # noqa: F401
    except ImportError:
        pytest.skip('Flask not installed; skipping API registration test')

    from actifix.api import create_app

    repo_root = Path(__file__).resolve().parents[1]
    app = create_app(project_root=repo_root)
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/modules/dev_assistant/health" in rules
    assert "/modules/dev_assistant/chat" in rules


def test_ollama_installation_and_model():
    # Skip if Ollama CLI is not available
    if not shutil.which('ollama'):
        pytest.skip('Ollama CLI not available; skipping model test')
    # Verify the CLI works
    proc = subprocess.run(['ollama', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0, f"Ollama CLI returned {proc.returncode}"
    # Verify the model is listed
    list_proc = subprocess.run(['ollama', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert list_proc.returncode == 0, f"Failed to list Ollama models: {list_proc.stderr}"
    assert 'qwen2.5-coder:7b-instruct' in list_proc.stdout, f"Model 'qwen2.5-coder:7b-instruct' not found in ollama list"


def test_ollama_server_running():
    try:
        try:
            with urllib.request.urlopen('http://localhost:11434', timeout=5) as resp:
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            status = exc.code
        # It may return 404 if root path is not handled; any response means server is up
        assert status in (200, 404), f"Unexpected status code: {status}"
    except urllib.error.URLError as exc:
        pytest.fail(f"Failed to connect to Ollama server: {exc}")
