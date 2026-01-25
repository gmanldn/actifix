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

from actifix.modules.base import ModuleBase
from actifix.modules.config import get_module_config
from actifix.raise_af import TicketPriority

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8080,
    "max_query_length": 2000,
    "history_limit": 100,
}

MODULE_METADATA = {
    "name": "modules.hollogram",
    "version": "1.0.0",
    "description": "AI-powered medical research assistant for educational purposes.",
    "capabilities": {"ai": True, "health": True, "research": True},
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


def run_gui(*args, **kwargs) -> None:
    """This module does not provide a GUI."""
    raise NotImplementedError("Hollogram does not implement a graphical interface.")
