"""PokerTool module stub that registers the planned integration surface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority

from .core import PokerToolAnalysisError, evaluate_hand
from actifix.modules.base import ModuleBase

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8060,
}

MODULE_METADATA = {
    "name": "pokertool",
    "version": "0.1.0",
    "description": "PokerTool port with real-time analysis, modern web interface and "
    "detection system hooks hosted by Actifix.",
    "capabilities": {
        "health": True,
        "analysis_api": True,
    },
    "data_access": {"state_dir": True},
    "permissions": ["logging", "fs_read"],
}

MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for the PokerTool scaffolding."""
    return ModuleBase(
        module_key="pokertool",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _stub_response(message: str, extra: Optional[dict[str, object]] = None) -> dict[str, object]:
    payload: dict[str, object] = {"status": "ok", "message": message}
    if extra:
        payload.update(extra)
    return payload


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/pokertool",
) -> "Blueprint":
    """Create the Flask blueprint that shields the PokerTool surface."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, jsonify, request, Response

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("pokertool", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index() -> Response:
            return jsonify(
                _stub_response(
                    "PokerTool integration landing point.",
                    {"module": helper.module_id},
                )
            )

        @blueprint.route("/health")
        def health() -> Response:
            return jsonify(helper.health_response())

        @blueprint.route("/api/status")
        def status() -> Response:
            return jsonify(
                _stub_response(
                    "Analysis services are warming up.",
                    {
                        "host": resolved_host,
                        "port": resolved_port,
                        "analysis_ready": False,
                    },
                )
            )

        @blueprint.route("/api/analysis", methods=["POST"])
        def analysis() -> Response:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                helper.record_module_error(
                    message="Analysis endpoint requires a JSON payload.",
                    source="modules.pokertool.__init__:analysis",
                    error_type="PayloadError",
                    priority=TicketPriority.P3,
                )
                return jsonify(
                    {"status": "error", "message": "JSON body expected for analysis."}
                ), 400
            hand = payload.get("hand") or []
            board = payload.get("board") or []
            try:
                analysis_result = evaluate_hand(hand, board)
            except PokerToolAnalysisError as exc:
                helper.record_module_error(
                    message=f"Invalid analysis payload: {exc}",
                    source="modules.pokertool.__init__:analysis",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": str(exc)}), 400
            except Exception as exc:
                helper.record_module_error(
                    message=f"Unexpected analysis failure: {exc}",
                    source="modules.pokertool.__init__:analysis",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P1,
                )
                raise
            return jsonify(
                _stub_response("Analysis payload processed.", {"analysis": analysis_result})
            )

        helper.log_gui_init(resolved_host, resolved_port, extra={"module": helper.module_id})
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create PokerTool blueprint: {exc}",
            source="modules.pokertool.__init__:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create a Flask application for the PokerTool module."""
    helper = _module_helper(project_root)
    try:
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_blueprint(
            project_root=project_root,
            host=host,
            port=port,
            url_prefix=None,
        )
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create PokerTool app: {exc}",
            source="modules.pokertool.__init__:create_app",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def run_service(
    host: Optional[str] = None,
    port: Optional[int] = None,
    project_root: Optional[Union[str, Path]] = None,
    debug: bool = False,
) -> None:
    """Spin up the Flask service for local verification."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "POKERTOOL_SERVICE_START",
            f"PokerTool service running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": helper.module_id},
            source="modules.pokertool.__init__:run_service",
        )
        app.run(host=resolved_host, port=resolved_port, debug=debug)
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start PokerTool service: {exc}",
            source="modules.pokertool.__init__:run_service",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise
