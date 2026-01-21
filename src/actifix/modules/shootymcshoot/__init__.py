"""ShootyMcShoot module - React hello world holding page on localhost:8040."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority

from actifix.modules.base import ModuleBase

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8040,
}
ACCESS_RULE = "local-only"
MODULE_METADATA = {
    "name": "modules.shootymcshoot",
    "version": "1.0.0",
    "description": "ShootyMcShoot React hello world holding page.",
    "capabilities": {"gui": True, "health": True},
    "data_access": {"state_dir": True},
    "network": {"external_requests": False},
    "permissions": ["logging", "fs_read"]
}
MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for ShootyMcShoot."""
    return ModuleBase(
        module_key="shootymcshoot",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/shootymcshoot",
) -> Blueprint:
    """Create the Flask blueprint that serves the ShootyMcShoot React app."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response  # Local import keeps Flask optional

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("shootymcshoot", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            return Response(_HTML_PAGE, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create ShootyMcShoot blueprint: {exc}",
            source="modules/shootymcshoot/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create the Flask app that serves the ShootyMcShoot app."""
    try:
        from flask import Flask  # Local import to keep optional dependency optional

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create ShootyMcShoot app: {exc}",
            source="modules/shootymcshoot/__init__.py:create_app",
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
    """Run the ShootyMcShoot app on localhost."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "SHOOTY_GUI_START",
            f"ShootyMcShoot GUI running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": "modules.shootymcshoot"},
            source="modules.shootymcshoot.run_gui",
        )
        app.run(host=resolved_host, port=resolved_port, debug=debug)
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start ShootyMcShoot GUI: {exc}",
            source="modules/shootymcshoot/__init__.py:run_gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ShootyMcShoot</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f1e8;
      --panel: #fffaf0;
      --ink: #2c2a24;
      --accent: #c44f2c;
      --accent-2: #1c6e6a;
      --muted: #6f6b61;
      --border: #d6cfbf;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: radial-gradient(circle at top, #fff8e6, #f2efe2 60%, #e7e0cf);
      color: var(--ink);
      min-height: 100vh;
    }
    .app {
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 24px;
      text-align: center;
    }
    h1 {
      font-size: 64px;
      font-weight: 800;
      letter-spacing: -2px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0 0 24px;
    }
    .subtitle {
      font-size: 20px;
      color: var(--muted);
      margin: 0 0 48px;
      font-weight: 400;
    }
    .status {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin: 32px 0;
      font-size: 18px;
    }
    .coming-soon {
      font-size: 24px;
      color: var(--accent);
      margin-top: 32px;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect } = React;

    function App() {
      const [status, setStatus] = useState('loading');

      useEffect(() => {
        setTimeout(() => setStatus('ready'), 1000);
      }, []);

      return (
        <div className="app">
          <h1>🎯 ShootyMcShoot</h1>
          <p className="subtitle">Actifix Module - localhost:8040</p>
          <div className="status">
            Status: <strong>{status === 'ready' ? '🚀 Live & Loaded' : '🔄 Initializing...'}</strong>
          </div>
          <p>React-powered holding page. Full shooty action coming soon!</p>
          <div className="coming-soon">Watch this space 👀</div>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    run_gui()
