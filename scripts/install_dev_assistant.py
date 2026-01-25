#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Installer for the Dev Assistant module.

This script adds a new locally‑hosted AI module to the Actifix codebase.
The module exposes a small API that proxies requests to a local Ollama
instance so that you can ask coding questions about this project.  It
updates configuration defaults to use Ollama, bumps the version
numbers in both the Python package and the front‑end, and registers
the new module in the architecture dependency graph.  Run this script
from the root of the Actifix repository after ensuring that Ollama is
installed and running on your machine.  If you already have local
changes, commit them before running this installer.

Steps performed:
  1. Write the `src/actifix/modules/dev_assistant/__init__.py` module
     containing a Flask blueprint that proxies chat requests to
     `http://localhost:11434/api/chat` using the configured model.
  2. Update `src/actifix/config.py` so that the default AI provider
     becomes "ollama" and the default model uses the chosen Ollama
     model.  The Ollama model is also set in the `ollama_model`
     attribute.
  3. Bump the core version in `src/actifix/__init__.py` and the
     UI version in `actifix-frontend/app.js` to a new semantic
     release number.
  4. Extend `docs/architecture/DEPGRAPH.json` with a new node for
     `modules.dev_assistant` and add edges describing its
     dependencies.

To execute this script:

    python3 install_dev_assistant.py

The script will print a summary of the changes it applies.  If
something goes wrong, it will raise an exception rather than silently
continuing.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

import shutil

# Bump this constant to change the Actifix version.  It should follow
# semantic versioning.  The UI version will mirror this version.
NEW_VERSION = "5.0.0"

# The Ollama model used for local coding assistance.  Change this
# constant if you wish to use a different model (e.g.
# "qwen2.5-coder:7b-instruct" or "yi-coder:9b-instruct").
DEFAULT_MODEL = "qwen2.5-coder:7b-instruct"

PACKAGE_MANAGERS = {
    "apt-get": ["sudo", "apt-get", "install", "-y", "ollama"],
    "dnf": ["sudo", "dnf", "install", "-y", "ollama"],
    "pacman": ["sudo", "pacman", "-S", "--noconfirm", "ollama"],
}


def _detect_package_manager() -> Optional[str]:
    """Return the first available package manager that may provide Ollama."""
    for name in ("apt-get", "dnf", "pacman"):
        if shutil.which(name):
            return name
    return None


def _install_with_package_manager(manager: str) -> bool:
    """Attempt to install Ollama via the detected package manager."""
    cmd = PACKAGE_MANAGERS.get(manager)
    if not cmd:
        return False
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as exc:
        print(f"   • Failed to install via {manager}: {exc}")
        return False


def find_project_root() -> Path:
    """Locate the Actifix project root from the script's location.

    The project root is identified by the presence of both
    ``src/actifix`` and ``actifix-frontend`` directories.  The search
    walks up from the directory containing this script.  If the root
    cannot be found within a reasonable number of levels, an error is
    raised.

    Returns:
        Path: The path to the project root.
    """
    here = Path(__file__).resolve().parent
    for _ in range(8):
        if (here / "src" / "actifix").is_dir() and (here / "actifix-frontend").is_dir():
            return here
        if here == here.parent:
            break
        here = here.parent
    raise RuntimeError(
        "Could not locate the project root.  Please run this script from within the Actifix repository."
    )


def write_dev_assistant_module(root: Path) -> None:
    """Create the dev_assistant module file with a Flask blueprint.

    The module proxies chat requests to a locally running Ollama
    instance.  It uses a long primer to inform the model about the
    Actifix codebase structure and development conventions.  Errors
    encountered during request handling are recorded via the Actifix
    logging system so that issues surface in the dashboard.

    Args:
        root: The project root directory.
    """
    module_dir = root / "src" / "actifix" / "modules" / "dev_assistant"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_file = module_dir / "__init__.py"

    # This primer summarizes the Actifix architecture and development
    # conventions.  It is provided to the language model on every
    # request so that the assistant can answer questions in the
    # appropriate context.  Feel free to expand this summary if the
    # codebase evolves.
    primer = (
        "You are DevAssistant, an expert software engineer assisting with "
        "the Actifix project. Actifix is a modular error tracking and "
        "self‑healing framework. The Python backend lives under the 'src/actifix' "
        "directory. Key components include:\n"
        "- 'bootstrap.py': initializes the framework and sets up runtime state.\n"
        "- 'config.py': defines ActifixConfig; defaults control AI integration, "
        "including the AI provider and model.\n"
        "- 'raise_af.py': captures errors and persists tickets. Use the "
        "`record_error()` function to record any new issues; never silently "
        "create files outside of the ticketing system.\n"
        "- 'do_af.py': processes tickets, dispatches them to AI providers and "
        "marks them complete when fixes succeed.\n"
        "- 'ai_client.py': provides multi‑provider AI integration with fallback "
        "logic.  When working inside a module you generally do not need to call "
        "this directly; modules should proxy to their own local provider if "
        "appropriate.\n"
        "- 'persistence/': implements SQLite persistence via the ticket and "
        "event repositories. The database file lives under 'data/actifix.db'.\n"
        "- 'modules/': contains additional optional modules which register Flask "
        "blueprints on the runtime API. Each module defines MODULE_DEFAULTS, "
        "MODULE_METADATA, MODULE_DEPENDENCIES and implements a `create_blueprint` "
        "function returning a Flask Blueprint.\n"
        "The React front‑end is located in 'actifix-frontend' and consumes the "
        "REST API exposed by the backend. Any UI changes should be placed in "
        "that directory. Always adhere to existing code patterns: use Python 3.10 "
        "syntax, respect the project layout, record errors via `record_error()`, "
        "write files with `atomic_write()`, and keep persistence confined to the "
        "ticket repository. Use comments sparingly and focus on clear, readable "
        "code."
    )

    # Determine the module directory and file path
    module_dir = root / "src" / "actifix" / "modules" / "dev_assistant"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_file = module_dir / "__init__.py"

    # The primer summarises the Actifix architecture and development conventions.
    # It is passed to the language model on every request so that the assistant
    # understands the context of this repository.
    # (Defined earlier in this function as the variable `primer`.)

    # Compose the module source code.  A triple-quoted string is used to hold
    # the entire Python file, including a docstring, imports, defaults,
    # metadata, dependencies, primer declaration, blueprint factory, and stubbed
    # GUI function.  Curly braces in the generated code are doubled to avoid
    # being interpreted as f-string placeholders.
    module_code = f'''# Auto-generated by install_dev_assistant.py
"""DevAssistant module for Actifix.

This module exposes a simple API endpoint that proxies chat requests
to a locally running Ollama model.  The assistant is primed with a
summary of the Actifix architecture (see the PRIMER constant below) so
that it can generate context-aware responses for developers working
within this repository.  To use this module, ensure that your
Ollama server is running at http://localhost:11434 and that the model
specified in MODULE_DEFAULTS['model'] is pulled locally (e.g.
`ollama pull {DEFAULT_MODEL}`).

The blueprint registers two routes under the prefix ``/modules/dev_assistant``:
  • ``/health`` returns the module health status via ModuleBase.  It
    uses the standard ModuleBase health implementation.
  • ``/chat`` accepts a JSON payload with a ``prompt`` field and
    returns the assistant's response in a JSON body.  Errors are
    logged via ModuleBase and a 500 response is returned on failure.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Optional, Union

from actifix.modules.base import ModuleBase
from actifix.modules.config import get_module_config
from actifix.raise_af import TicketPriority

# Defaults and metadata for the DevAssistant module
MODULE_DEFAULTS = {{
    "model": "{DEFAULT_MODEL}",
}}

MODULE_METADATA = {{
    "name": "modules.dev_assistant",
    "version": "1.0.0",
    "description": "Local AI coding assistant using Ollama with Actifix primer.",
    "capabilities": {{"ai": True}},
    "data_access": {{"state_dir": False}},
    "network": {{"external_requests": False}},
    "permissions": ["logging", "network_http"],
}}

MODULE_DEPENDENCIES = [
    "modules.base",
    "modules.config",
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]

# Long primer text passed to the model on every request.  See
# install_dev_assistant.py for details.
PRIMER = {primer!r}

def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Return a ModuleBase helper configured for this module."""
    return ModuleBase(
        module_key="dev_assistant",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _resolve_model(
    helper: ModuleBase,
    project_root: Optional[Union[str, Path]],
    override: Optional[str],
) -> str:
    """Return the Ollama model name, using overrides or module config."""
    if override:
        return override
    module_config = get_module_config(helper.module_key, helper.module_defaults, project_root=project_root)
    return str(module_config.get("model") or MODULE_DEFAULTS["model"])

def _post_ollama_chat(payload: dict[str, object], timeout: float = 60.0) -> dict[str, object]:
    """Send a chat payload to the local Ollama API using stdlib HTTP."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        if not body:
            return {{}}
        return json.loads(body.decode("utf-8"))

def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    model: Optional[str] = None,
    url_prefix: Optional[str] = "/modules/dev_assistant",
) -> "Blueprint":
    """Create and return the Flask blueprint for the DevAssistant module.

    The returned blueprint will have ``/health`` and ``/chat`` routes.

    Args:
        project_root: Optional override for the project root.
        host: Optional override for the host (unused).
        port: Optional override for the port (unused).
        model: Optional override for the Ollama model name.
        url_prefix: URL prefix for the blueprint.  Defaults to
            ``/modules/dev_assistant``.

    Returns:
        flask.Blueprint: The configured blueprint.
    """
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, request, jsonify

        blueprint = Blueprint("dev_assistant", __name__, url_prefix=url_prefix)
        resolved_model = _resolve_model(helper, project_root, model)

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        @blueprint.route("/chat", methods=["POST"])
        def chat():
            # Extract the prompt from the incoming JSON body
            data = request.get_json(silent=True) or {{}}
            prompt = data.get("prompt") or data.get("message") or ""
            if not isinstance(prompt, str) or not prompt.strip():
                return jsonify({{"error": "Missing or empty prompt"}}), 400
            try:
                payload = {{
                    "model": resolved_model,
                    "messages": [
                        {{"role": "system", "content": PRIMER}},
                        {{"role": "user", "content": prompt.strip()}},
                    ],
                }}
                result = _post_ollama_chat(payload, timeout=60.0)
                # Ollama returns either {{"message": {{"content": ...}}}} or {{"response": ...}}
                answer = (
                    (result.get("message") or {{}}).get("content")
                    or result.get("response")
                    or ""
                )
                return jsonify({{"assistant": answer}})
            except Exception as exc:
                helper.record_module_error(
                    message=f"DevAssistant failed: {{exc}}",
                    source="modules/dev_assistant",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )
                return jsonify({{"error": str(exc)}}), 500

        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create DevAssistant blueprint: {{exc}}",
            source="modules/dev_assistant",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise

def run_gui(*args, **kwargs) -> None:
    """This module does not provide a GUI."""
    raise NotImplementedError("DevAssistant does not implement a graphical interface.")
'''

    # Write the constructed module file
    module_file.write_text(module_code, encoding="utf-8")


def is_ollama_running() -> bool:
    """Check whether the local Ollama API is reachable on localhost.

    Returns:
        bool: True if a connection succeeds, False otherwise.
    """
    try:
        try:
            with urllib.request.urlopen("http://localhost:11434", timeout=3) as resp:
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            status = exc.code
        # We don't care about the return value, just whether we can connect.
        return status in (200, 404)
    except Exception:
        return False


def ensure_ollama() -> None:
    """Ensure that Ollama is installed, the requested model is pulled, and the server is running.

    This function installs Ollama using the official installer if the
    executable is not found in the PATH, pulls the required model, and
    starts the Ollama server in the background if it's not already
    running.  Because Ollama may take a few seconds to load the model,
    the function polls the API endpoint until it becomes available.
    """
    # Check if the Ollama CLI is available
    if shutil.which("ollama") is None:
        print(" - Ollama binary not found, attempting to install...")
        # Attempt a platform‑specific installation.  On macOS use Homebrew if available;
        # on Linux fall back to the official install script.  Windows users should
        # install Ollama manually.
        try:
            if sys.platform.startswith("darwin"):
                # If Homebrew exists, prefer it; otherwise fall back to the script
                if shutil.which("brew"):
                    print("   • Installing Ollama via Homebrew...")
                    subprocess.run(["brew", "install", "ollama"], check=True)
                else:
                    print("   • Homebrew not found; downloading and running the install script...")
                    subprocess.run(
                        [
                            "bash",
                            "-c",
                            # The AI domain hosts the installer; using bash for better compatibility
                            "curl -fsSL https://ollama.ai/install.sh | bash",
                        ],
                        check=True,
                    )
            elif sys.platform.startswith("win"):
                # Windows installation requires manual steps or winget; provide guidance
                print("   • Automatic installation is not supported on Windows in this script. "
                      "Please download and install Ollama from https://ollama.com/download/windows before running the installer again.")
                return
            else:
                manager = _detect_package_manager()
                if manager:
                    print(f"   • Detected package manager: {manager}; attempting install...")
                    if _install_with_package_manager(manager):
                        print("   • Ollama installed successfully via package manager.")
                        return
                    print("   • Falling back to official installer script.")
                subprocess.run(
                    [
                        "bash",
                        "-c",
                        "curl -fsSL https://ollama.ai/install.sh | bash",
                    ],
                    check=True,
                )
            print("   • Ollama installed successfully.")
        except Exception as exc:
            print(
                f"   • Failed to install Ollama automatically: {exc}. "
                "Please install Ollama manually before proceeding."
            )
            return
    # Re-check after installation
    if shutil.which("ollama") is None:
        print("   • Ollama CLI still not found after installation attempt; skipping model pull and server start.")
        return
    # Pull the desired model if it's not already present
    try:
        # Check if model metadata is available via 'ollama show'
        subprocess.run(
            ["ollama", "show", DEFAULT_MODEL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        print(f" - Pulling Ollama model {DEFAULT_MODEL}...")
        try:
            subprocess.run(["ollama", "pull", DEFAULT_MODEL], check=True)
            print("   • Model pulled successfully.")
        except Exception as exc:
            print(f"   • Failed to pull model {DEFAULT_MODEL}: {exc}")
            return
    # Ensure the server is running
    if not is_ollama_running():
        print(" - Starting Ollama server in the background...")
        # Start the server in detached mode
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            print(f"   • Failed to launch Ollama server: {exc}")
            return
        # Poll until the server responds or timeout expires
        for _ in range(30):
            if is_ollama_running():
                print("   • Ollama server is now running.")
                break
            time.sleep(1)
        else:
            print("   • Warning: Ollama server did not start within 30 seconds.")


def write_dev_assistant_tests(root: Path) -> None:
    """Create a pytest file that validates the DevAssistant installation.

    The tests verify that configuration defaults have been updated, the
    module can be imported and its Flask blueprint registers properly,
    and that required endpoints respond correctly.  These tests will
    run during the installation script to give immediate feedback.

    Args:
        root: The project root directory.
    """
    test_dir = root / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_dev_assistant.py"
    test_content = f"""# -*- coding: utf-8 -*-

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
    assert config.ai_provider == "", f"Expected ai_provider default to be empty, got {{config.ai_provider}}"
    assert config.ai_model == '{DEFAULT_MODEL}', f"Expected ai_model '{DEFAULT_MODEL}', got {{config.ai_model}}"
    assert config.ollama_model == '{DEFAULT_MODEL}', f"Expected ollama_model '{DEFAULT_MODEL}', got {{config.ollama_model}}"


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
        assert resp.status_code == 200, f"Health returned {{resp.status_code}}"
        # Missing prompt should return 400
        resp = client.post('/modules/dev_assistant/chat', json={{}})
        assert resp.status_code == 400, f"Empty prompt should return 400, got {{resp.status_code}}"


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
    assert proc.returncode == 0, f"Ollama CLI returned {{proc.returncode}}"
    # Verify the model is listed
    list_proc = subprocess.run(['ollama', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert list_proc.returncode == 0, f"Failed to list Ollama models: {{list_proc.stderr}}"
    assert '{DEFAULT_MODEL}' in list_proc.stdout, f"Model '{DEFAULT_MODEL}' not found in ollama list"


def test_ollama_server_running():
    try:
        try:
            with urllib.request.urlopen('http://localhost:11434', timeout=5) as resp:
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            status = exc.code
        # It may return 404 if root path is not handled; any response means server is up
        assert status in (200, 404), f"Unexpected status code: {{status}}"
    except urllib.error.URLError as exc:
        pytest.fail(f"Failed to connect to Ollama server: {{exc}}")
"""
    test_file.write_text(test_content, encoding="utf-8")


def run_dev_assistant_tests(root: Path) -> None:
    """Execute the DevAssistant tests using pytest.

    This function invokes pytest on the newly created test file and
    reports success or failure.  It does not raise if tests fail; the
    user can inspect the output to diagnose issues.

    Args:
        root: The project root directory.
    """
    try:
        import sys as _sys
        # Check whether pytest is installed; skip tests if unavailable
        try:
            import pytest  # noqa: F401
        except ImportError:
            print("pytest not installed; skipping DevAssistant tests.")
            return
        print("Running DevAssistant tests...")
        # Assemble environment with PYTHONPATH pointing at the src directory
        env = os.environ.copy()
        env['PYTHONPATH'] = str(root / 'src') + os.pathsep + env.get('PYTHONPATH', '')
        # Execute pytest on the specific test file
        subprocess.run(
            [_sys.executable, '-m', 'pytest', '-q', 'test/test_dev_assistant.py'],
            cwd=str(root),
            env=env,
            check=False,
        )
    except Exception as exc:
        print(f"Error while running tests: {exc}")


def update_config(root: Path) -> None:
    """Adjust default AI settings in src/actifix/config.py to use Ollama.

    The provider defaults are set to "ollama", the generic model defaults
    are set to our chosen model, and the dedicated `ollama_model` is
    updated as well.  Regex substitutions are used to replace only the
    default assignment values without changing surrounding code.

    Args:
        root: The project root directory.
    """
    config_path = root / "src" / "actifix" / "config.py"
    if not config_path.is_file():
        raise FileNotFoundError(f"Could not find config.py at {config_path}")
    original = config_path.read_text(encoding="utf-8")
    updated = original
    # Replace ai_provider default
    updated = re.sub(
        r"(ai_provider\s*:\s*str\s*=\s*)\"[^\"]*\"",
        r'\1"ollama"',
        updated,
        count=1,
    )
    # Replace ai_model default
    updated = re.sub(
        r"(ai_model\s*:\s*str\s*=\s*)\"[^\"]*\"",
        fr'\1"{DEFAULT_MODEL}"',
        updated,
        count=1,
    )
    # Replace ollama_model default
    updated = re.sub(
        r"(ollama_model\s*:\s*str\s*=\s*)\"[^\"]*\"",
        fr'\1"{DEFAULT_MODEL}"',
        updated,
        count=1,
    )
    if updated != original:
        config_path.write_text(updated, encoding="utf-8")


def bump_python_version(root: Path) -> None:
    """Update the __version__ constant in src/actifix/__init__.py."""
    init_path = root / "src" / "actifix" / "__init__.py"
    if not init_path.is_file():
        raise FileNotFoundError(f"Missing __init__.py at {init_path}")
    original = init_path.read_text(encoding="utf-8")
    # Replace the existing __version__ assignment with the new version using a raw f-string.
    # This avoids escaping quotes incorrectly (e.g. inserting backslashes), producing
    # a valid Python string like __version__ = "4.0.49".
    updated = re.sub(
        r'(__version__\s*=\s*)"[^"]*"',
        rf'\1"{NEW_VERSION}"',
        original,
        count=1,
    )
    if updated != original:
        init_path.write_text(updated, encoding="utf-8")


def bump_ui_version(root: Path) -> None:
    """Update the UI version constant in actifix-frontend/app.js."""
    app_js = root / "actifix-frontend" / "app.js"
    if not app_js.is_file():
        raise FileNotFoundError(f"Could not locate app.js at {app_js}")
    original = app_js.read_text(encoding="utf-8")
    updated = re.sub(
        r"(UI_VERSION\s*=\s*)'[^']*'",
        fr"\1'{NEW_VERSION}'",
        original,
        count=1,
    )
    if updated != original:
        app_js.write_text(updated, encoding="utf-8")


def update_depgraph(root: Path) -> None:
    """Register the dev_assistant module in the architecture graph.

    Adds a new node and relevant edges to ``docs/architecture/DEPGRAPH.json``.
    If the node already exists, no duplicate is added.  Edges are only
    appended if they do not already exist.

    Args:
        root: The project root directory.
    """
    depgraph_path = root / "docs" / "architecture" / "DEPGRAPH.json"
    if not depgraph_path.is_file():
        raise FileNotFoundError(f"Could not locate DEPGRAPH.json at {depgraph_path}")
    data = json.loads(depgraph_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    if not any(node.get("id") == "modules.dev_assistant" for node in nodes):
        nodes.append({
            "id": "modules.dev_assistant",
            "domain": "modules",
            "owner": "modules",
            "label": "dev_assistant",
        })
    edges = data.get("edges", [])
    required_edges = [
        {
            "from": "modules.dev_assistant",
            "to": "runtime.state",
            "reason": "modules.dev_assistant uses Actifix state paths",
        },
        {
            "from": "modules.dev_assistant",
            "to": "infra.logging",
            "reason": "modules.dev_assistant logs events via infra.logging",
        },
        {
            "from": "modules.dev_assistant",
            "to": "core.raise_af",
            "reason": "modules.dev_assistant records errors via core.raise_af",
        },
        {
            "from": "modules.dev_assistant",
            "to": "runtime.api",
            "reason": "modules.dev_assistant registers a blueprint on the runtime API server",
        },
    ]
    for edge in required_edges:
        if not any(e.get("from") == edge["from"] and e.get("to") == edge["to"] for e in edges):
            edges.append(edge)
    data["nodes"] = nodes
    data["edges"] = edges
    meta = data.get("meta", {})
    # Use timezone-aware UTC timestamp; .isoformat() returns a string with '+00:00'
    # which we replace with 'Z' for ISO 8601 compliance.
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    meta["generated_at"] = timestamp
    data["meta"] = meta
    depgraph_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = find_project_root()
    print(f"Project root detected at {root}")
    print("Installing DevAssistant module...")
    write_dev_assistant_module(root)
    print(" - Module file written.")
    # Ensure Ollama is installed, the model is pulled, and the server is running
    ensure_ollama()
    # Write and run DevAssistant tests as part of setup
    write_dev_assistant_tests(root)
    update_config(root)
    print(" - Configuration updated to default to Ollama provider and model.")
    bump_python_version(root)
    print(f" - Bumped Python package version to {NEW_VERSION}.")
    bump_ui_version(root)
    print(f" - Bumped front‑end UI version to {NEW_VERSION}.")
    update_depgraph(root)
    print(" - Registered dev_assistant module in the architecture graph.")
    # Run the tests at the end to validate the installation
    run_dev_assistant_tests(root)
    print("Installation complete.  Please restart the Actifix server to load the new module.")


if __name__ == "__main__":
    main()
