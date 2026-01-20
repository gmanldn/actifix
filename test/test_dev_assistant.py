# -*- coding: utf-8 -*-

import importlib
import json
import subprocess
import sys

import pytest
import requests

import shutil

from actifix.config import load_config


def test_config_defaults():
    config = load_config()
    assert config.ai_provider.lower() == 'ollama', f"Expected ai_provider 'ollama', got {config.ai_provider}"
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
        resp = client.get('/modules/dev-assistant/health')
        assert resp.status_code == 200, f"Health returned {resp.status_code}"
        # Missing prompt should return 400
        resp = client.post('/modules/dev-assistant/chat', json={})
        assert resp.status_code == 400, f"Empty prompt should return 400, got {resp.status_code}"


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
        resp = requests.get('http://localhost:11434', timeout=5)
        # It may return 404 if root path is not handled; any response means server is up
        assert resp.status_code in (200, 404), f"Unexpected status code: {resp.status_code}"
    except requests.RequestException as exc:
        pytest.skip(f"Ollama server not reachable ({exc}); skipping dependent test")
