"""ArtClass module for teaching art with a localhost GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

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
    "name": "modules.artclass",
    "version": "1.0.0",
    "description": "Art teaching module with interactive React-based GUI.",
    "capabilities": {
        "gui": True,
        "health": True,
    },
    "data_access": {
        "state_dir": True,
    },
    "network": {
        "external_requests": False,
    },
    "permissions": ["logging", "fs_read"],
}
MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for ArtClass."""
    return ModuleBase(
        module_key="artclass",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/artclass",
) -> Blueprint:
    """Create the Flask blueprint that serves the ArtClass GUI."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response  # Local import keeps Flask optional

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("artclass", __name__, url_prefix=url_prefix)

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
            message=f"Failed to create ArtClass blueprint: {exc}",
            source="modules/artclass/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create the Flask app that serves the ArtClass GUI."""
    try:
        from flask import Flask  # Local import to keep optional dependency optional

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create ArtClass GUI app: {exc}",
            source="modules/artclass/__init__.py:create_app",
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
    """Run the ArtClass GUI on localhost."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "ARTCLASS_GUI_START",
            f"ArtClass GUI running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": "modules.artclass"},
            source="modules.artclass.run_gui",
        )
        app.run(host=resolved_host, port=resolved_port, debug=debug)
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start ArtClass GUI: {exc}",
            source="modules/artclass/__init__.py:run_gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ArtClass Module</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f9f7f4;
      --panel: #ffffff;
      --ink: #1a1a1a;
      --accent: #d4722f;
      --accent-2: #2e7d76;
      --muted: #6b6b6b;
      --border: #e0ddd8;
      --success: #2e7d76;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", sans-serif;
      background: linear-gradient(135deg, #f5f2ed 0%, #ede9e2 100%);
      color: var(--ink);
      min-height: 100vh;
    }
    .app {
      max-width: 1200px;
      margin: 0 auto;
      padding: 48px 32px;
    }
    header {
      margin-bottom: 48px;
    }
    .header-content {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
    }
    .header-title {
      flex: 1;
    }
    .subtitle {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 2.5px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    h1 {
      font-size: 48px;
      margin: 0;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: var(--ink);
    }
    h2 {
      font-size: 24px;
      margin: 0 0 16px 0;
      font-weight: 600;
      color: var(--ink);
    }
    .intro-section {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 32px;
      margin-bottom: 32px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .intro-text {
      font-size: 16px;
      line-height: 1.6;
      color: var(--ink);
      margin: 0;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    .card h3 {
      margin: 0 0 12px 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--ink);
    }
    .card p {
      margin: 0 0 16px 0;
      font-size: 14px;
      color: var(--muted);
      line-height: 1.5;
    }
    .button {
      appearance: none;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      cursor: pointer;
      background: linear-gradient(135deg, #d4722f, #c1631f);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(212, 114, 47, 0.25);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .button:hover:not([disabled]) {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(212, 114, 47, 0.35);
    }
    .button:active:not([disabled]) {
      transform: translateY(0px);
    }
    .button[disabled] {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .button.secondary {
      background: linear-gradient(135deg, #2e7d76, #1f5850);
      box-shadow: 0 4px 12px rgba(46, 125, 118, 0.25);
    }
    .button.secondary:hover:not([disabled]) {
      box-shadow: 0 6px 16px rgba(46, 125, 118, 0.35);
    }
    .status-badge {
      display: inline-block;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(46, 125, 118, 0.1);
      color: var(--success);
      margin-top: 12px;
    }
    .feature-list {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .feature-list li {
      padding: 8px 0;
      font-size: 14px;
      color: var(--ink);
      position: relative;
      padding-left: 24px;
    }
    .feature-list li:before {
      content: "✓";
      position: absolute;
      left: 0;
      color: var(--success);
      font-weight: bold;
    }
    .footer {
      text-align: center;
      padding-top: 32px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="header-content">
        <div class="header-title">
          <div class="subtitle">Actifix Module</div>
          <h1>ArtClass</h1>
        </div>
      </div>
    </header>

    <div class="intro-section">
      <h2>Welcome to ArtClass</h2>
      <p class="intro-text">
        An interactive art teaching module built with React. Learn fundamental art concepts, techniques, and practice sketching and design fundamentals in an engaging, interactive environment.
      </p>
      <div class="status-badge">Active & Ready</div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Sketch Basics</h3>
        <p>Master fundamental sketching techniques including line work, proportions, shading, and perspective drawing.</p>
        <button class="button" onclick="alert('Sketch Basics module coming soon!')">Explore</button>
      </div>

      <div class="card">
        <h3>Color Theory</h3>
        <p>Understand color harmony, color mixing, palettes, and how colors interact in visual composition.</p>
        <button class="button" onclick="alert('Color Theory module coming soon!')">Explore</button>
      </div>

      <div class="card">
        <h3>Composition</h3>
        <p>Learn about layout, balance, framing, and principles of composition for creating impactful artwork.</p>
        <button class="button" onclick="alert('Composition module coming soon!')">Explore</button>
      </div>

      <div class="card">
        <h3>Digital Art</h3>
        <p>Introduction to digital tools, tablets, software, and techniques for creating digital artwork.</p>
        <button class="button" onclick="alert('Digital Art module coming soon!')">Explore</button>
      </div>
    </div>

    <div class="intro-section">
      <h2>Key Features (In Development)</h2>
      <ul class="feature-list">
        <li>Interactive drawing canvas</li>
        <li>Real-time feedback and guidance</li>
        <li>Step-by-step tutorials</li>
        <li>Progress tracking</li>
        <li>Gallery of student work</li>
        <li>Resource library and references</li>
      </ul>
    </div>

    <div class="footer">
      <p>ArtClass v1.0.0 • Part of Actifix • Powered by React on port 8040</p>
    </div>
  </div>

  <script>
    // Placeholder for future React component initialization
    console.log("ArtClass module loaded and ready");
    document.addEventListener("DOMContentLoaded", function() {
      console.log("DOM ready - ready for interactive features");
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    run_gui()
