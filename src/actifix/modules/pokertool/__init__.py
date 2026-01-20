"""PokerTool module stub that registers the planned integration surface."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Optional, TYPE_CHECKING, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority

from actifix.modules.base import ModuleBase
from .core import PokerToolAnalysisError, evaluate_hand
from .detector import DetectionPipeline
from .solvers import (
    PokerToolSolverError,
    compute_nash_equilibrium,
    estimate_icm_value,
)
from .ml import (
    PokerToolMLError,
    active_learning_hint,
    build_opponent_model,
)

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


DETECTION_PIPELINE = DetectionPipeline()


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


def _format_sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _stream_detection_events() -> Iterable[str]:
    last_sequence = -1
    while True:
        summary = DETECTION_PIPELINE.summary()
        latest = DETECTION_PIPELINE.latest_update()
        if latest and latest.sequence != last_sequence:
            last_sequence = latest.sequence
            yield _format_sse("update", DETECTION_PIPELINE.payload_for(latest))
            continue
        yield _format_sse("status", summary)
        if not summary["active"]:
            break
        time.sleep(0.75)
    yield _format_sse("status", {"active": False, "note": "Stream closed"})


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/pokertool",
) -> "Blueprint":
    """Create the Flask blueprint that shields the PokerTool surface."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response, jsonify, request

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

        @blueprint.route("/api/solvers/nash", methods=["POST"])
        def solvers_nash() -> Response:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                helper.record_module_error(
                    message="Solver endpoint requires a JSON payload.",
                    source="modules.pokertool.__init__:solvers_nash",
                    error_type="PayloadError",
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": "JSON body expected."}), 400
            try:
                recommendation = compute_nash_equilibrium(
                    payload.get("hand") or [],
                    payload.get("board"),
                )
            except PokerToolSolverError as exc:
                helper.record_module_error(
                    message=f"Nash computation failed: {exc}",
                    source="modules.pokertool.__init__:solvers_nash",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": str(exc)}), 400
            return jsonify(
                _stub_response(
                    "Nash computation completed.",
                    {"recommendation": recommendation.__dict__},
                )
            )

        @blueprint.route("/api/solvers/icm", methods=["POST"])
        def solvers_icm() -> Response:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                helper.record_module_error(
                    message="ICM endpoint requires a JSON payload.",
                    source="modules.pokertool.__init__:solvers_icm",
                    error_type="PayloadError",
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": "JSON body expected."}), 400
            try:
                result = estimate_icm_value(
                    payload.get("stacks") or [],
                    payload.get("payouts") or [],
                )
            except PokerToolSolverError as exc:
                helper.record_module_error(
                    message=f"ICM estimation failed: {exc}",
                    source="modules.pokertool.__init__:solvers_icm",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": str(exc)}), 400
            return jsonify(
                _stub_response("ICM estimation complete.", result)
            )

        @blueprint.route("/api/ml/opponent", methods=["POST"])
        def ml_opponent() -> Response:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                helper.record_module_error(
                    message="Opponent model endpoint requires a JSON payload.",
                    source="modules.pokertool.__init__:ml_opponent",
                    error_type="PayloadError",
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": "JSON body expected."}), 400
            try:
                profile = build_opponent_model(payload.get("history") or [])
            except PokerToolMLError as exc:
                helper.record_module_error(
                    message=f"Opponent model failed: {exc}",
                    source="modules.pokertool.__init__:ml_opponent",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": str(exc)}), 400
            return jsonify(
                _stub_response("Opponent model ready.", profile.__dict__)
            )

        @blueprint.route("/api/ml/learn", methods=["POST"])
        def ml_learn() -> Response:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                helper.record_module_error(
                    message="Active learning endpoint requires a JSON payload.",
                    source="modules.pokertool.__init__:ml_learn",
                    error_type="PayloadError",
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": "JSON body expected."}), 400
            try:
                hint = active_learning_hint(payload.get("scores") or [])
            except PokerToolMLError as exc:
                helper.record_module_error(
                    message=f"Active learning failed: {exc}",
                    source="modules.pokertool.__init__:ml_learn",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                return jsonify({"status": "error", "message": str(exc)}), 400
            return jsonify(_stub_response("Active learning hint produced.", hint))

        @blueprint.route("/api/detect/start", methods=["POST"])
        def detect_start() -> Response:
            try:
                DETECTION_PIPELINE.start()
                return jsonify(_stub_response("Detection pipeline started.", DETECTION_PIPELINE.summary()))
            except RuntimeError as exc:
                helper.record_module_error(
                    message=f"Detection pipeline start failed: {exc}",
                    source="modules.pokertool.__init__:detect_start",
                    error_type="RuntimeError",
                    priority=TicketPriority.P3,
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(exc),
                            "active": DETECTION_PIPELINE.active,
                        }
                    ),
                    409,
                )

        @blueprint.route("/api/detect/stop", methods=["POST"])
        def detect_stop() -> Response:
            DETECTION_PIPELINE.stop()
            return jsonify(_stub_response("Detection pipeline stopped.", DETECTION_PIPELINE.summary()))

        @blueprint.route("/api/detect/status")
        def detect_status() -> Response:
            latest = DETECTION_PIPELINE.latest_update()
            payload = DETECTION_PIPELINE.payload_for(latest)
            payload.update(DETECTION_PIPELINE.summary())
            return jsonify(_stub_response("Detection status snapshot.", payload))

        @blueprint.route("/api/detect/stream")
        def detect_stream() -> Response:
            return Response(_stream_detection_events(), mimetype="text/event-stream")

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
