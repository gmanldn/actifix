"""Hollogram module for Actifix.

An AI-powered medical research assistant that provides educational medical
information with proper safety disclaimers.

The blueprint registers routes under the prefix ``/modules/hollogram``:
  - ``/health`` returns the module health status via ModuleBase
  - ``/disclaimer`` returns the medical disclaimer text
  - ``/topics`` returns available research topic categories
  - ``/research`` (POST) processes research queries with AI
  - ``/history`` (GET) retrieves past research queries
  - ``/history/<id>`` (DELETE) removes a history entry
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from actifix.log_utils import log_event
from actifix.modules.base import ModuleBase
from actifix.modules.config import get_module_config
from actifix.raise_af import TicketPriority

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8050,
    "max_query_length": 2000,
    "history_limit": 100,
}

MODULE_METADATA = {
    "name": "modules.hollogram",
    "version": "1.0.0",
    "description": "AI-powered medical research assistant for educational purposes.",
    "capabilities": {"ai": True, "health": True, "research": True, "gui": True},
    "data_access": {"state_dir": True},
    "network": {"external_requests": True},
    "permissions": ["logging", "network_http"],
}

MODULE_DEPENDENCIES = [
    "modules.base",
    "modules.config",
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
    "core.ai_client",
]

ACCESS_RULE = "local-only"

MEDICAL_DISCLAIMER = """
IMPORTANT MEDICAL DISCLAIMER

The information provided by Hollogram is for educational and research purposes only.
It is NOT intended as a substitute for professional medical advice, diagnosis, or treatment.

- Always seek the advice of your physician or other qualified health provider with
  any questions you may have regarding a medical condition.
- Never disregard professional medical advice or delay in seeking it because of
  information obtained through this service.
- If you think you may have a medical emergency, call your doctor, go to the
  emergency department, or call emergency services immediately.
- Reliance on any information provided by Hollogram is solely at your own risk.

This service does not establish a doctor-patient relationship.
""".strip()

RESEARCH_PRIMER = """You are Hollogram, a medical research assistant for educational purposes.

GUIDELINES:
- Information is for educational/research purposes only
- Never provide diagnosis or treatment recommendations
- Recommend consulting healthcare professionals for personal health concerns
- Cite sources when possible using [Source: description] format
- Flag queries that appear to seek urgent medical advice
- Be accurate, balanced, and evidence-based
- Explain medical terminology in accessible language
- Note any limitations or uncertainties in current medical knowledge

RESPONSE FORMAT:
Provide clear, well-structured educational information. Include citations where possible.
If the query appears to be seeking personal medical advice, remind the user to consult
a healthcare professional.
"""

TOPIC_CATEGORIES = [
    {"id": "anatomy", "name": "Anatomy", "description": "Body structures and systems"},
    {"id": "conditions", "name": "Conditions", "description": "Diseases, disorders, and syndromes"},
    {"id": "medications", "name": "Medications", "description": "Drugs, dosages, and interactions"},
    {"id": "procedures", "name": "Procedures", "description": "Medical and surgical procedures"},
    {"id": "terminology", "name": "Terminology", "description": "Medical terms and definitions"},
    {"id": "research_methods", "name": "Research Methods", "description": "Clinical research methodologies"},
    {"id": "clinical_trials", "name": "Clinical Trials", "description": "Trial phases and design"},
]

URGENT_PATTERNS = [
    r"\b(emergency|urgent|immediately|right now|911|ambulance)\b",
    r"\b(chest pain|heart attack|stroke|can.t breathe|difficulty breathing)\b",
    r"\b(suicide|suicidal|kill myself|end my life)\b",
    r"\b(overdose|overdosed|poisoning|severe allergic)\b",
    r"\b(severe bleeding|won.t stop bleeding|bleeding.+stop)\b",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Return a ModuleBase helper configured for this module."""
    return ModuleBase(
        module_key="hollogram",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _get_db_path(helper: ModuleBase) -> Path:
    """Get the path to the history database."""
    paths = helper.get_paths()
    return paths.state_dir / "hollogram_history.db"


def _init_database(db_path: Path) -> None:
    """Initialize the SQLite database with required tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hollogram_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                category TEXT,
                response TEXT NOT NULL,
                provider TEXT,
                citations TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp
            ON hollogram_history(timestamp DESC)
        """)
        conn.commit()
    finally:
        conn.close()


def _save_history_entry(
    db_path: Path,
    query: str,
    category: str,
    response: str,
    provider: str,
    citations: List[str],
    history_limit: int = 100,
) -> int:
    """Save a research query to history and return the entry ID."""
    _init_database(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()
        citations_json = json.dumps(citations)

        cursor.execute(
            """
            INSERT INTO hollogram_history (query, category, response, provider, citations, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (query, category, response, provider, citations_json, timestamp),
        )
        entry_id = cursor.lastrowid

        # Cleanup old entries beyond limit
        cursor.execute(
            """
            DELETE FROM hollogram_history
            WHERE id NOT IN (
                SELECT id FROM hollogram_history
                ORDER BY timestamp DESC
                LIMIT ?
            )
            """,
            (history_limit,),
        )

        conn.commit()
        return entry_id
    finally:
        conn.close()


def _get_history(db_path: Path, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve research history entries."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, query, category, response, provider, citations, timestamp
            FROM hollogram_history
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        history = []
        for row in rows:
            try:
                citations = json.loads(row["citations"]) if row["citations"] else []
            except (json.JSONDecodeError, TypeError):
                citations = []

            history.append({
                "id": row["id"],
                "query": row["query"],
                "category": row["category"],
                "response": row["response"][:200] + "..." if len(row["response"]) > 200 else row["response"],
                "provider": row["provider"],
                "citations": citations,
                "timestamp": row["timestamp"],
            })

        return history
    finally:
        conn.close()


def _get_history_entry(db_path: Path, entry_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single history entry by ID."""
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, query, category, response, provider, citations, timestamp
            FROM hollogram_history
            WHERE id = ?
            """,
            (entry_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        try:
            citations = json.loads(row["citations"]) if row["citations"] else []
        except (json.JSONDecodeError, TypeError):
            citations = []

        return {
            "id": row["id"],
            "query": row["query"],
            "category": row["category"],
            "response": row["response"],
            "provider": row["provider"],
            "citations": citations,
            "timestamp": row["timestamp"],
        }
    finally:
        conn.close()


def _delete_history_entry(db_path: Path, entry_id: int) -> bool:
    """Delete a history entry by ID. Returns True if deleted."""
    if not db_path.exists():
        return False

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM hollogram_history WHERE id = ?",
            (entry_id,),
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()


def _detect_urgent_query(query: str) -> bool:
    """Check if query appears to be seeking urgent medical advice."""
    query_lower = query.lower()
    for pattern in URGENT_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    return False


def _extract_citations(response: str) -> List[str]:
    """Extract citation references from AI response."""
    citations = []
    # Match [Source: description] patterns
    source_matches = re.findall(r'\[Source:\s*([^\]]+)\]', response)
    citations.extend(source_matches)

    # Match [Citation: description] patterns
    citation_matches = re.findall(r'\[Citation:\s*([^\]]+)\]', response)
    citations.extend(citation_matches)

    # Match numbered references like [1], [2]
    ref_matches = re.findall(r'\[(\d+)\]', response)
    for ref in ref_matches:
        citations.append(f"Reference {ref}")

    return list(set(citations))  # Remove duplicates


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/hollogram",
) -> "Blueprint":
    """Create and return the Flask blueprint for the Hollogram module.

    The returned blueprint will have health, disclaimer, topics, research,
    and history routes.

    Args:
        project_root: Optional override for the project root.
        host: Optional override for the host.
        port: Optional override for the port.
        url_prefix: URL prefix for the blueprint.

    Returns:
        flask.Blueprint: The configured blueprint.
    """
    helper = _module_helper(project_root)

    try:
        from flask import Blueprint, request, jsonify

        blueprint = Blueprint("hollogram", __name__, url_prefix=url_prefix)
        db_path = _get_db_path(helper)

        module_config = get_module_config(
            helper.module_key,
            helper.module_defaults,
            project_root=helper.project_root,
        )
        max_query_length = int(module_config.get("max_query_length", MODULE_DEFAULTS["max_query_length"]))
        history_limit = int(module_config.get("history_limit", MODULE_DEFAULTS["history_limit"]))

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        @blueprint.route("/disclaimer")
        def disclaimer():
            return jsonify({
                "disclaimer": MEDICAL_DISCLAIMER,
                "version": MODULE_METADATA["version"],
            })

        @blueprint.route("/topics")
        def topics():
            return jsonify({
                "topics": TOPIC_CATEGORIES,
                "count": len(TOPIC_CATEGORIES),
            })

        @blueprint.route("/research", methods=["POST"])
        def research():
            data = request.get_json(silent=True) or {}

            query = data.get("query", "").strip()
            category = data.get("category", "").strip()
            disclaimer_accepted = data.get("disclaimer_accepted", False)

            # Validation
            if not query:
                return jsonify({"error": "Missing or empty query"}), 400

            if len(query) > max_query_length:
                return jsonify({
                    "error": f"Query exceeds maximum length of {max_query_length} characters"
                }), 400

            if not disclaimer_accepted:
                return jsonify({
                    "error": "You must accept the medical disclaimer to proceed",
                    "disclaimer": MEDICAL_DISCLAIMER,
                }), 400

            # Validate category if provided
            valid_categories = [t["id"] for t in TOPIC_CATEGORIES]
            if category and category not in valid_categories:
                return jsonify({
                    "error": f"Invalid category. Valid options: {', '.join(valid_categories)}"
                }), 400

            # Check for urgent queries
            if _detect_urgent_query(query):
                return jsonify({
                    "success": False,
                    "urgent": True,
                    "message": "Your query appears to describe an urgent medical situation.",
                    "action_required": (
                        "If you are experiencing a medical emergency, please:\n"
                        "- Call emergency services (911 in the US)\n"
                        "- Go to your nearest emergency room\n"
                        "- Contact your healthcare provider immediately\n\n"
                        "This service cannot provide emergency medical assistance."
                    ),
                    "resources": {
                        "emergency": "911",
                        "suicide_prevention": "988 (Suicide & Crisis Lifeline)",
                        "poison_control": "1-800-222-1222",
                    },
                    "disclaimer": MEDICAL_DISCLAIMER,
                }), 200

            # Build the AI prompt
            category_context = ""
            if category:
                cat_info = next((t for t in TOPIC_CATEGORIES if t["id"] == category), None)
                if cat_info:
                    category_context = f"\nTopic Category: {cat_info['name']} ({cat_info['description']})\n"

            full_prompt = f"{RESEARCH_PRIMER}{category_context}\nResearch Query: {query}"

            # Call AI provider
            try:
                from actifix.ai_client import get_ai_client

                ai_client = get_ai_client()

                # Create a ticket-like structure for the AI client
                ticket_info = {
                    "id": "HOLLOGRAM-RESEARCH",
                    "priority": "P3",
                    "error_type": "research_query",
                    "message": full_prompt,
                    "source": "hollogram",
                    "stack_trace": "",
                }

                response = ai_client.generate_fix(ticket_info)

                if response.success:
                    ai_response = response.content
                    provider = response.provider.value if response.provider else "unknown"
                else:
                    # Fallback response
                    ai_response = (
                        "I apologize, but I'm unable to process your research query at this time. "
                        "Please try again later or consult authoritative medical resources such as:\n"
                        "- PubMed (pubmed.ncbi.nlm.nih.gov)\n"
                        "- MedlinePlus (medlineplus.gov)\n"
                        "- CDC (cdc.gov)\n"
                        "- WHO (who.int)\n\n"
                        f"Error: {response.error}"
                    )
                    provider = "fallback"

            except Exception as exc:
                helper.record_module_error(
                    message=f"AI research query failed: {exc}",
                    source="modules/hollogram",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )
                ai_response = (
                    "I apologize, but I'm unable to process your research query at this time. "
                    "Please try again later."
                )
                provider = "error"

            # Extract citations from response
            citations = _extract_citations(ai_response)

            # Save to history
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                entry_id = _save_history_entry(
                    db_path,
                    query,
                    category or "general",
                    ai_response,
                    provider,
                    citations,
                    history_limit,
                )
            except Exception as exc:
                helper.record_module_error(
                    message=f"Failed to save research history: {exc}",
                    source="modules/hollogram",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P3,
                )
                entry_id = None

            return jsonify({
                "success": True,
                "query": query,
                "category": category or "general",
                "response": ai_response,
                "citations": citations,
                "provider": provider,
                "disclaimer": MEDICAL_DISCLAIMER,
                "timestamp": timestamp,
                "history_id": entry_id,
            })

        @blueprint.route("/history")
        def history():
            limit = request.args.get("limit", 50, type=int)
            limit = min(max(1, limit), history_limit)

            entries = _get_history(db_path, limit)

            return jsonify({
                "success": True,
                "history": entries,
                "count": len(entries),
                "limit": limit,
            })

        @blueprint.route("/history/<int:entry_id>")
        def history_entry(entry_id: int):
            entry = _get_history_entry(db_path, entry_id)

            if not entry:
                return jsonify({"error": "History entry not found"}), 404

            return jsonify({
                "success": True,
                "entry": entry,
            })

        @blueprint.route("/history/<int:entry_id>", methods=["DELETE"])
        def delete_history_entry(entry_id: int):
            deleted = _delete_history_entry(db_path, entry_id)

            if not deleted:
                return jsonify({"error": "History entry not found"}), 404

            return jsonify({
                "success": True,
                "message": f"History entry {entry_id} deleted",
            })

        return blueprint

    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create Hollogram blueprint: {exc}",
            source="modules/hollogram",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


def create_gui_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = None,
) -> "Blueprint":
    """Create the Flask blueprint that serves the Hollogram GUI."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("hollogram_gui", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            return Response(_GUI_HTML, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        helper.log_gui_init(resolved_host, resolved_port, event_name="HOLLOGRAM_GUI_INIT")
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create Hollogram GUI blueprint: {exc}",
            source="modules/hollogram/__init__.py:create_gui_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_gui_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create the Flask app that serves the Hollogram GUI."""
    try:
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_gui_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create Hollogram GUI app: {exc}",
            source="modules/hollogram/__init__.py:create_gui_app",
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
    """Run the Hollogram GUI on the configured host/port."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_gui_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "HOLLOGRAM_GUI_START",
            f"Hollogram GUI running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": "modules.hollogram"},
            source="modules.hollogram.run_gui",
        )
        app.run(host=resolved_host, port=resolved_port, debug=debug)
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start Hollogram GUI: {exc}",
            source="modules/hollogram/__init__.py:run_gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_GUI_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hollogram Research Console</title>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: light;
      --bg: #f3efe6;
      --panel: #fbf8f2;
      --ink: #1f1e1a;
      --muted: #6d685f;
      --accent: #0f6b5a;
      --accent-2: #d96f3a;
      --border: #d7cfc1;
      --shadow: 0 24px 70px rgba(17, 14, 4, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 12% 10%, #ffffff 0%, #f7f1e2 35%, #ece5d7 68%),
        linear-gradient(120deg, #f9f4ea, #efe8da);
      color: var(--ink);
      min-height: 100vh;
    }
    header {
      padding: 42px 24px 12px;
      text-align: center;
    }
    h1 {
      font-family: "Fraunces", serif;
      font-size: clamp(36px, 6vw, 64px);
      margin: 0;
      letter-spacing: -1px;
    }
    h1 span {
      color: var(--accent);
    }
    .tagline {
      margin-top: 12px;
      color: var(--muted);
      font-size: 16px;
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 24px 60px;
      display: grid;
      gap: 24px;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 24px;
      box-shadow: var(--shadow);
    }
    .panel h2 {
      margin-top: 0;
      font-size: 20px;
      letter-spacing: 0.4px;
    }
    .stack {
      display: grid;
      gap: 14px;
    }
    label {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
    }
    input, select, textarea {
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--border);
      font-size: 15px;
      font-family: inherit;
      background: #fff;
      color: var(--ink);
    }
    textarea { min-height: 160px; resize: vertical; }
    .row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .row > * { flex: 1; min-width: 180px; }
    .button {
      appearance: none;
      border: none;
      background: linear-gradient(135deg, var(--accent), #0b4a3e);
      color: #fff;
      padding: 12px 18px;
      border-radius: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      box-shadow: 0 12px 28px rgba(15, 107, 90, 0.3);
    }
    .button.secondary {
      background: linear-gradient(135deg, var(--accent-2), #b35126);
      box-shadow: 0 12px 28px rgba(217, 111, 58, 0.3);
    }
    .button:disabled { opacity: 0.6; cursor: not-allowed; }
    .button:hover:not(:disabled) { transform: translateY(-1px); }
    .note {
      font-size: 13px;
      color: var(--muted);
    }
    .output {
      white-space: pre-wrap;
      line-height: 1.6;
      font-size: 15px;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chip {
      padding: 6px 10px;
      border-radius: 999px;
      background: #fff;
      border: 1px solid var(--border);
      font-size: 12px;
    }
    .history-item {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px;
      background: #fff;
      display: grid;
      gap: 6px;
    }
    .history-meta {
      font-size: 12px;
      color: var(--muted);
    }
    .status {
      padding: 8px 12px;
      border-radius: 12px;
      background: #fef5ea;
      border: 1px solid #f2d7be;
      color: #9a4d1e;
      font-size: 13px;
    }
    @media (max-width: 768px) {
      main { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Hollogram <span>Research Console</span></h1>
    <div class="tagline">Educational medical research assistant with safety-first responses.</div>
  </header>
  <main>
    <section class="panel stack">
      <h2>Research Brief</h2>
      <div class="stack">
        <label for="apiBase">API Base URL</label>
        <input id="apiBase" type="text" value="http://127.0.0.1:5001" />
        <div class="row">
          <div class="stack">
            <label for="category">Topic category</label>
            <select id="category"></select>
          </div>
          <div class="stack">
            <label for="historyLimit">History limit</label>
            <input id="historyLimit" type="number" min="1" max="100" value="20" />
          </div>
        </div>
        <label for="query">Research question</label>
        <textarea id="query" placeholder="Ask about anatomy, medications, procedures, or research methods..."></textarea>
        <label>
          <input id="disclaimer" type="checkbox" />
          I understand this is educational information only.
        </label>
        <button class="button" id="sendBtn">Submit research query</button>
        <div class="status" id="status">Ready.</div>
      </div>
    </section>

    <section class="panel stack">
      <h2>Response</h2>
      <div class="output" id="response">Your response will appear here.</div>
      <div>
        <h3>Citations</h3>
        <div class="chips" id="citations"></div>
      </div>
    </section>

    <section class="panel stack">
      <h2>Recent History</h2>
      <button class="button secondary" id="refreshHistory">Refresh history</button>
      <div class="stack" id="historyList"></div>
    </section>
  </main>

  <script>
    const apiBaseInput = document.getElementById("apiBase");
    const categorySelect = document.getElementById("category");
    const queryInput = document.getElementById("query");
    const disclaimerInput = document.getElementById("disclaimer");
    const sendBtn = document.getElementById("sendBtn");
    const statusEl = document.getElementById("status");
    const responseEl = document.getElementById("response");
    const citationsEl = document.getElementById("citations");
    const historyBtn = document.getElementById("refreshHistory");
    const historyList = document.getElementById("historyList");
    const historyLimitInput = document.getElementById("historyLimit");

    function setStatus(text, busy = false) {
      statusEl.textContent = text;
      sendBtn.disabled = busy;
    }

    async function fetchJson(path, options = {}) {
      const url = apiBaseInput.value.replace(/\\/$/, "") + path;
      const resp = await fetch(url, options);
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `HTTP ${resp.status}`);
      }
      return resp.json();
    }

    async function loadCategories() {
      try {
        const data = await fetchJson("/modules/hollogram/topics");
        categorySelect.innerHTML = "";
        data.topics.forEach(topic => {
          const opt = document.createElement("option");
          opt.value = topic.id;
          opt.textContent = `${topic.name} — ${topic.description}`;
          categorySelect.appendChild(opt);
        });
      } catch (err) {
        setStatus(`Failed to load topics: ${err.message}`);
      }
    }

    function renderCitations(list) {
      citationsEl.innerHTML = "";
      if (!list || !list.length) {
        const chip = document.createElement("div");
        chip.className = "chip";
        chip.textContent = "No citations returned.";
        citationsEl.appendChild(chip);
        return;
      }
      list.forEach(item => {
        const chip = document.createElement("div");
        chip.className = "chip";
        chip.textContent = item;
        citationsEl.appendChild(chip);
      });
    }

    async function runQuery() {
      const query = queryInput.value.trim();
      if (!query) {
        setStatus("Add a research question first.");
        return;
      }
      if (!disclaimerInput.checked) {
        setStatus("Please accept the disclaimer before continuing.");
        return;
      }
      setStatus("Submitting research query...", true);
      responseEl.textContent = "";
      try {
        const payload = {
          query,
          category: categorySelect.value,
          disclaimer_accepted: disclaimerInput.checked
        };
        const data = await fetchJson("/modules/hollogram/research", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        if (data.urgent) {
          responseEl.textContent = data.message + "\\n\\n" + data.action_required;
          renderCitations([]);
          setStatus("Urgent guidance returned.");
          return;
        }
        responseEl.textContent = data.response || "No response returned.";
        renderCitations(data.citations || []);
        setStatus("Done.");
        await loadHistory();
      } catch (err) {
        responseEl.textContent = "Error: " + err.message;
        renderCitations([]);
        setStatus("Query failed.");
      } finally {
        sendBtn.disabled = false;
      }
    }

    async function loadHistory() {
      historyList.innerHTML = "";
      const limit = Math.max(1, Math.min(100, Number(historyLimitInput.value || 20)));
      try {
        const data = await fetchJson(`/modules/hollogram/history?limit=${limit}`);
        if (!data.history || !data.history.length) {
          const item = document.createElement("div");
          item.className = "note";
          item.textContent = "No history recorded yet.";
          historyList.appendChild(item);
          return;
        }
        data.history.forEach(entry => {
          const card = document.createElement("div");
          card.className = "history-item";
          card.innerHTML = `
            <div><strong>${entry.query}</strong></div>
            <div class="history-meta">${entry.category} · ${entry.timestamp}</div>
            <div class="note">${entry.response}</div>
          `;
          historyList.appendChild(card);
        });
      } catch (err) {
        const item = document.createElement("div");
        item.className = "note";
        item.textContent = "History unavailable: " + err.message;
        historyList.appendChild(item);
      }
    }

    sendBtn.addEventListener("click", runQuery);
    historyBtn.addEventListener("click", loadHistory);

    loadCategories();
    loadHistory();
  </script>
</body>
</html>
"""
