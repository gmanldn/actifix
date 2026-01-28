"""Scaffolded module for Actifix."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.modules.base import ModuleBase
from actifix.raise_af import TicketPriority

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8110,
}

ACCESS_RULE = "local-only"

MODULE_METADATA = {
    "name": "modules.testmanifest",
    "version": "0.1.0",
    "description": "Scaffolded module created by Actifix CLI.",
    "capabilities": {"gui": True, "health": True},
    "data_access": {"state_dir": True},
    "network": {"external_requests": False},
    "permissions": ["logging", "fs_read"],
}

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
        module_key="testmanifest",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/testmanifest",
) -> "Blueprint":
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, jsonify

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        if url_prefix:
            blueprint = Blueprint("testmanifest", __name__, url_prefix=url_prefix)
        else:
            blueprint = Blueprint("testmanifest", __name__)

        @blueprint.route("/")
        @helper.error_boundary(source="modules/testmanifest/__init__.py:index")
        def index():
            return jsonify({"module": "testmanifest", "status": "ok"})

        health_handler = helper.health_handler()

        @blueprint.route("/health")
        def health():
            return health_handler()

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create testmanifest blueprint: {exc}",
            source="modules/testmanifest/__init__.py:create_blueprint",
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
            message=f"Failed to create testmanifest GUI app: {exc}",
            source="modules/testmanifest/__init__.py:create_app",
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
