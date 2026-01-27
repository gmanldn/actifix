#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module scaffolding helpers for Actifix CLI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from actifix.log_utils import atomic_write

_MODULE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_module_name(name: str) -> str:
    clean = (name or "").strip().lower()
    if not clean:
        raise ValueError("module name is required")
    if clean.startswith("modules."):
        clean = clean.split(".", 1)[1]
    if not _MODULE_NAME_PATTERN.match(clean):
        raise ValueError(
            "module name must be lowercase alphanumeric/underscore and start with a letter"
        )
    return clean


def _module_template(module_key: str, host: str, port: int) -> str:
    module_id = f"modules.{module_key}"
    return f'''"""Scaffolded module for Actifix."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.modules.base import ModuleBase
from actifix.raise_af import TicketPriority

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {{
    "host": "{host}",
    "port": {port},
}}

ACCESS_RULE = "local-only"

MODULE_METADATA = {{
    "name": "{module_id}",
    "version": "0.1.0",
    "description": "Scaffolded module created by Actifix CLI.",
    "capabilities": {{"gui": True, "health": True}},
    "data_access": {{"state_dir": True}},
    "network": {{"external_requests": False}},
    "permissions": ["logging", "fs_read"],
}}

MODULE_DEPENDENCIES = [
    "modules.base",
    "modules.config",
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    return ModuleBase(
        module_key="{module_key}",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/{module_key}",
) -> "Blueprint":
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, jsonify

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        if url_prefix:
            blueprint = Blueprint("{module_key}", __name__, url_prefix=url_prefix)
        else:
            blueprint = Blueprint("{module_key}", __name__)

        @blueprint.route("/")
        def index():
            return jsonify({{"module": "{module_key}", "status": "ok"}})

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create {module_key} blueprint: {{exc}}",
            source="modules/{module_key}/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    try:
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create {module_key} GUI app: {{exc}}",
            source="modules/{module_key}/__init__.py:create_app",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def run_gui(
    host: Optional[str] = None,
    port: Optional[int] = None,
    project_root: Optional[Union[str, Path]] = None,
    debug: bool = False,
) -> None:
    app = create_app(project_root=project_root, host=host, port=port)
    resolved_host = host or MODULE_DEFAULTS["host"]
    resolved_port = port or MODULE_DEFAULTS["port"]
    app.run(host=resolved_host, port=resolved_port, debug=debug)
'''


def _test_template(module_key: str) -> str:
    return f'''from actifix.testing import create_module_test_client


def test_{module_key}_health():
    client = create_module_test_client("{module_key}", url_prefix=None)
    response = client.get("/health")
    assert response.status_code == 200
'''


def create_module_scaffold(
    module_name: str,
    *,
    project_root: Path,
    host: str = "127.0.0.1",
    port: int = 8100,
    force: bool = False,
) -> dict:
    """Create a module skeleton (code + tests) under the project root."""
    module_key = _validate_module_name(module_name)
    module_dir = project_root / "src" / "actifix" / "modules" / module_key
    module_file = module_dir / "__init__.py"
    test_file = project_root / "test" / f"test_module_{module_key}.py"

    if module_dir.exists() and not force:
        raise FileExistsError(f"Module directory already exists: {module_dir}")

    module_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(module_file, _module_template(module_key, host, port))
    atomic_write(test_file, _test_template(module_key))

    return {
        "module_key": module_key,
        "module_dir": str(module_dir),
        "module_file": str(module_file),
        "test_file": str(test_file),
    }
