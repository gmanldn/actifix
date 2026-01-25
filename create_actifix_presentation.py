#!/usr/bin/env python3
"""
Create a comprehensive 40-page ODF presentation showcasing Actifix for developers.
This script generates a presentation with detailed features, architecture, and use cases.
"""

from odf.opendocument import OpenDocumentPresentation
from odf.style import Style, ParagraphProperties, TextProperties, GraphicProperties
from odf.draw import Page, Frame, TextBox
from odf.text import P, Span
from odf.presentation import Notes
from datetime import datetime
import os

# Color scheme
COLORS = {
    "primary": "#2563eb",  # Blue
    "secondary": "#7c3aed",  # Purple
    "accent": "#059669",  # Green
    "warning": "#dc2626",  # Red
    "bg_light": "#f8fafc",
    "bg_dark": "#1e293b",
    "text_light": "#ffffff",
    "text_dark": "#0f172a",
}

def create_styles(doc):
    """Create styles for the presentation."""
    # Title style
    title_style = Style(name="Title", family="paragraph")
    title_style.addElement(TextProperties(
        fontSize="44pt",
        fontWeight="bold",
        color=COLORS["primary"]
    ))
    title_style.addElement(ParagraphProperties(
        marginBottom="12pt",
        textAlign="center"
    ))
    doc.automaticstyles.addElement(title_style)

    # Subtitle style
    subtitle_style = Style(name="Subtitle", family="paragraph")
    subtitle_style.addElement(TextProperties(
        fontSize="28pt",
        color=COLORS["secondary"]
    ))
    subtitle_style.addElement(ParagraphProperties(
        marginBottom="8pt",
        textAlign="center"
    ))
    doc.automaticstyles.addElement(subtitle_style)

    # Heading style
    heading_style = Style(name="Heading", family="paragraph")
    heading_style.addElement(TextProperties(
        fontSize="24pt",
        fontWeight="bold",
        color=COLORS["primary"]
    ))
    heading_style.addElement(ParagraphProperties(
        marginBottom="8pt"
    ))
    doc.automaticstyles.addElement(heading_style)

    # Subheading style
    subheading_style = Style(name="Subheading", family="paragraph")
    subheading_style.addElement(TextProperties(
        fontSize="18pt",
        fontWeight="bold",
        color=COLORS["secondary"]
    ))
    subheading_style.addElement(ParagraphProperties(
        marginBottom="6pt"
    ))
    doc.automaticstyles.addElement(subheading_style)

    # Body text style
    body_style = Style(name="Body", family="paragraph")
    body_style.addElement(TextProperties(
        fontSize="14pt",
        color=COLORS["text_dark"]
    ))
    body_style.addElement(ParagraphProperties(
        marginBottom="6pt",
        lineHeight="1.4"
    ))
    doc.automaticstyles.addElement(body_style)

    # Code style
    code_style = Style(name="Code", family="paragraph")
    code_style.addElement(TextProperties(
        fontSize="12pt",
        fontFamily="Monospace",
        color="#333333"
    ))
    code_style.addElement(ParagraphProperties(
        marginBottom="6pt",
        backgroundColor="#f1f5f9",
        padding="8pt",
        border="1pt solid #cbd5e1"
    ))
    doc.automaticstyles.addElement(code_style)

    # Bullet style
    bullet_style = Style(name="Bullet", family="paragraph")
    bullet_style.addElement(TextProperties(
        fontSize="14pt",
        color=COLORS["text_dark"]
    ))
    bullet_style.addElement(ParagraphProperties(
        marginBottom="4pt",
        lineHeight="1.4"
    ))
    doc.automaticstyles.addElement(bullet_style)

    # Highlight style
    highlight_style = Style(name="Highlight", family="paragraph")
    highlight_style.addElement(TextProperties(
        fontSize="16pt",
        fontWeight="bold",
        color=COLORS["accent"]
    ))
    highlight_style.addElement(ParagraphProperties(
        marginBottom="6pt"
    ))
    doc.automaticstyles.addElement(highlight_style)

    # Warning style
    warning_style = Style(name="Warning", family="paragraph")
    warning_style.addElement(TextProperties(
        fontSize="14pt",
        color=COLORS["warning"]
    ))
    warning_style.addElement(ParagraphProperties(
        marginBottom="6pt"
    ))
    doc.automaticstyles.addElement(warning_style)

    # Frame style for text boxes
    frame_style = Style(name="FrameStyle", family="graphic")
    frame_style.addElement(GraphicProperties(
        strokeColor=COLORS["primary"],
        fillColor=COLORS["bg_light"],
        strokeWidth="2pt"
    ))
    doc.automaticstyles.addElement(frame_style)


def create_page(doc, title, content_elements, page_number, total_pages):
    """Create a single presentation page."""
    page = Page(name=f"Page{page_number}")
    
    # Add title
    title_frame = Frame(name="TitleFrame", x="2cm", y="1cm", width="20cm", height="3cm")
    title_textbox = TextBox()
    title_textbox.addElement(P(text=title, stylename="Title"))
    title_frame.addElement(title_textbox)
    page.addElement(title_frame)
    
    # Add content
    content_y = 5
    for element in content_elements:
        if isinstance(element, dict):
            # Code block
            code_frame = Frame(name=f"CodeFrame{page_number}", x="2cm", y=f"{content_y}cm", width="20cm", height="2cm")
            code_textbox = TextBox()
            code_textbox.addElement(P(text=element["code"], stylename="Code"))
            code_frame.addElement(code_textbox)
            page.addElement(code_frame)
            content_y += 2.5
        elif isinstance(element, list):
            # Bullet points
            for bullet in element:
                bullet_frame = Frame(name=f"BulletFrame{page_number}{bullet[:10]}", x="2cm", y=f"{content_y}cm", width="20cm", height="0.8cm")
                bullet_textbox = TextBox()
                bullet_textbox.addElement(P(text=f"• {bullet}", stylename="Bullet"))
                bullet_frame.addElement(bullet_textbox)
                page.addElement(bullet_frame)
                content_y += 1
        elif element.startswith("HIGHLIGHT:"):
            # Highlight text
            highlight_frame = Frame(name=f"HighlightFrame{page_number}", x="2cm", y=f"{content_y}cm", width="20cm", height="1.5cm")
            highlight_textbox = TextBox()
            highlight_textbox.addElement(P(text=element[10:], stylename="Highlight"))
            highlight_frame.addElement(highlight_textbox)
            page.addElement(highlight_frame)
            content_y += 2
        elif element.startswith("WARNING:"):
            # Warning text
            warning_frame = Frame(name=f"WarningFrame{page_number}", x="2cm", y=f"{content_y}cm", width="20cm", height="1.5cm")
            warning_textbox = TextBox()
            warning_textbox.addElement(P(text=element[8:], stylename="Warning"))
            warning_frame.addElement(warning_textbox)
            page.addElement(warning_frame)
            content_y += 2
        else:
            # Regular text
            text_frame = Frame(name=f"TextFrame{page_number}{element[:10]}", x="2cm", y=f"{content_y}cm", width="20cm", height="1cm")
            text_textbox = TextBox()
            text_textbox.addElement(P(text=element, stylename="Body"))
            text_frame.addElement(text_textbox)
            page.addElement(text_frame)
            content_y += 1.2
    
    # Add page number
    page_num_frame = Frame(name=f"PageNumFrame{page_number}", x="18cm", y="26cm", width="4cm", height="1cm")
    page_num_textbox = TextBox()
    page_num_textbox.addElement(P(text=f"Page {page_number} of {total_pages}", stylename="Body"))
    page_num_frame.addElement(page_num_textbox)
    page.addElement(page_num_frame)
    
    doc.presentation.addElement(page)


def create_presentation():
    """Create the complete Actifix presentation."""
    doc = OpenDocumentPresentation()
    
    # Add metadata
    doc.meta.addElement(doc.MetaCreator(text="Actifix Presentation Generator"))
    doc.meta.addElement(doc.MetaTitle(text="Actifix - Self-Improving Error Management Framework"))
    doc.meta.addElement(doc.MetaDescription(text="Comprehensive presentation showcasing Actifix features and use cases for developers"))
    doc.meta.addElement(doc.MetaDate(text=datetime.now().isoformat()))
    
    # Create styles
    create_styles(doc)
    
    # Page 1: Title
    create_page(doc, "Actifix - Self-Improving Error Management Framework", [
        "The framework that tracks and improves itself",
        "HIGHLIGHT: Zero-dependency capture • AI-ready tickets • Self-development mode • Durable persistence",
        "",
        "Presented to: Development Teams",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "Version: 4.0.48"
    ], 1, 40)
    
    # Page 2: Table of Contents
    create_page(doc, "Table of Contents", [
        "1. Introduction & Overview",
        "2. Core Features",
        "3. Architecture & Design",
        "4. Error Capture System",
        "5. Ticket Management",
        "6. AI Integration",
        "7. Multi-Agent Workflow",
        "8. Module System",
        "9. Security Features",
        "10. Testing & Quality Gates",
        "11. Use Cases & Examples",
        "12. Getting Started",
        "13. Best Practices",
        "14. Roadmap & Future",
        "15. Conclusion"
    ], 2, 40)
    
    # Page 3: Introduction
    create_page(doc, "What is Actifix?", [
        "Actifix is a self-improving error management system that:",
        "",
        "• Captures prioritized tickets with rich context",
        "• Preserves operational context for AI copilots",
        "• Keeps development workflow auditable",
        "• Is stdlib-first and resilient under failure",
        "• Designed to feed AI systems with consistent context",
        "",
        "HIGHLIGHT: Every error becomes an actionable ticket with full context"
    ], 3, 40)
    
    # Page 4: Key Highlights
    create_page(doc, "Key Highlights", [
        "Zero-dependency capture:",
        "  • Drop-in without extra packages",
        "  • enable_actifix_capture() is all you need",
        "",
        "AI-ready tickets:",
        "  • Stack traces, file context, system state",
        "  • Remediation notes for AI processing",
        "",
        "Self-development mode:",
        "  • Framework can ticket its own regressions",
        "  • Keeps regressions visible during work",
        "",
        "Durable persistence:",
        "  • Atomic writes and fallback queues",
        "  • Database-first storage (SQLite)",
        "  • No data loss even during failures"
    ], 4, 40)
    
    # Page 5: Architecture Overview
    create_page(doc, "Architecture Overview", [
        "Core Modules:",
        "",
        "1. bootstrap - System initialization",
        "2. raise_af - Error capture & ticket creation",
        "3. do_af - Ticket processing & remediation",
        "4. persistence - SQLite-backed storage",
        "5. health - System health monitoring",
        "6. security - Authentication & rate limiting",
        "7. modules - User-facing experiences",
        "8. plugins - Extension system",
        "",
        "HIGHLIGHT: Lower layers cannot import higher layers (strict dependency rules)"
    ], 5, 40)
    
    # Page 6: Dependency Graph
    create_page(doc, "Dependency Graph", [
        "Runtime Layer:",
        "  bootstrap.main → runtime.config → infra.logging",
        "",
        "Infrastructure Layer:",
        "  infra.logging → infra.persistence.* → infra.health",
        "",
        "Core Layer:",
        "  core.raise_af → core.do_af → core.ai_client",
        "",
        "Security Layer:",
        "  security.auth → security.rate_limiter → security.ticket_throttler",
        "",
        "Plugin/Module Layer:",
        "  plugins.registry → modules.registry → modules.base",
        "",
        "HIGHLIGHT: Clean separation with enforced contracts"
    ], 6, 40)
    
    # Page 7: Error Capture Flow
    create_page(doc, "Error Capture Flow", [
        "1. Exception raised or manual capture call",
        "2. Raise_AF captures context (stack, files, system)",
        "3. Duplicate guard generation & checking",
        "4. Priority classification (P0-P4)",
        "5. Secret/PII redaction",
        "6. AI remediation notes generation",
        "7. Database persistence (data/actifix.db)",
        "8. Fallback queue if DB unavailable",
        "9. Ticket creation event logged",
        "",
        "HIGHLIGHT: Automatic deduplication prevents ticket floods"
    ], 7, 40)
    
    # Page 8: Priority Levels
    create_page(doc, "Priority Levels (P0-P4)", [
        "P0 - Critical (1hr SLA):",
        "  • Fatal errors, crashes, data corruption",
        "  • System down, data loss scenarios",
        "",
        "P1 - High (4hr SLA):",
        "  • Database issues, security, authentication",
        "  • Core functionality broken",
        "",
        "P2 - Medium (24hr SLA):",
        "  • Default for most errors",
        "  • Important but workaround exists",
        "",
        "P3 - Low (72hr SLA):",
        "  • Minor issues, cosmetic problems",
        "  • Warnings, deprecations",
        "",
        "P4 - Trivial (1wk SLA):",
        "  • Style, lint, format issues",
        "  • Nice-to-have improvements"
    ], 8, 40)
    
    # Page 9: Ticket Format
    create_page(doc, "Ticket Database Schema", [
        "SQLite Table: tickets",
        "",
        "Core Fields:",
        "  • id (TEXT PRIMARY KEY) - Unique ticket ID",
        "  • priority (TEXT) - P0-P4 classification",
        "  • error_type (TEXT) - Error class/type",
        "  • message (TEXT) - Descriptive message",
        "  • source (TEXT) - File:line location",
        "  • status (TEXT) - Open/Completed/Quarantined",
        "",
        "Context Fields:",
        "  • stack_trace (TEXT) - Full stack trace",
        "  • file_context (TEXT) - Relevant code snippets",
        "  • system_state (TEXT) - Environment snapshot",
        "  • ai_remediation_notes (TEXT) - AI processing hints",
        "",
        "Metadata Fields:",
        "  • created_at, updated_at (TIMESTAMP)",
        "  • duplicate_guard (TEXT UNIQUE)",
        "  • correlation_id (TEXT)",
        "  • owner, locked_by, lease_expires"
    ], 9, 40)
    
    # Page 10: Code Example - Basic Capture
    create_page(doc, "Code Example: Basic Error Capture", [
        "import sys",
        "import actifix",
        "",
        "# Enable Actifix capture",
        "actifix.enable_actifix_capture()",
        "",
        "try:",
        "    risky_operation()",
        "except Exception as exc:",
        "    actifix.record_error(",
        "        message=str(exc),",
        "        source=f'{__file__}:{sys._getframe().f_lineno}',",
        "        run_label='production-api',",
        "        error_type=type(exc).__name__,",
        "        capture_context=True,",
        "    )",
        "",
        "HIGHLIGHT: Context is automatically captured (stack, files, system state)"
    ], 10, 40)
    
    # Page 11: Code Example - Manual Recording
    create_page(doc, "Code Example: Manual Recording", [
        "from actifix.raise_af import record_error, TicketPriority",
        "",
        "# Record an error manually",
        "entry = record_error(",
        "    message='Database connection timeout',",
        "    source='database.py:42',",
        "    run_label='api-server',",
        "    error_type='TimeoutError',",
        "    priority=TicketPriority.P1,",
        "    capture_context=True,",
        ")",
        "",
        "if entry:",
        "    print(f'Ticket created: {entry.entry_id}')",
        "    print(f'Priority: {entry.priority.value}')",
        "    print(f'Duplicate Guard: {entry.duplicate_guard}')",
        "",
        "HIGHLIGHT: Returns None if duplicate detected (automatic deduplication)"
    ], 11, 40)
    
    # Page 12: Code Example - Self-Development Mode
    create_page(doc, "Code Example: Self-Development Mode", [
        "import actifix",
        "",
        "# Bootstrap Actifix for development tracking",
        "actifix.bootstrap_actifix_development()",
        "",
        "# Track development progress",
        "actifix.track_development_progress(",
        "    'Feature complete',",
        "    'AI telemetry integrated',",
        ")",
        "",
        "# The framework can ticket its own regressions",
        "try:",
        "    # Some development work",
        "    pass",
        "except Exception as exc:",
        "    actifix.record_error(",
        "        message=f'Regression detected: {exc}',",
        "        source='development.py:1',",
        "        error_type='Regression',",
        "        priority=actifix.TicketPriority.P2,",
        "    )",
        "",
        "HIGHLIGHT: Actifix monitors itself and creates tickets for its own issues"
    ], 12, 40)
    
    # Page 13: CLI Commands
    create_page(doc, "Core CLI Commands", [
        "System Management:",
        "  python3 -m actifix.main init",
        "  python3 -m actifix.main health",
        "  python3 -m actifix.main test",
        "",
        "Ticket Operations:",
        "  python3 -m actifix.main record ManualRecord 'message' 'module.py:42' --priority P2",
        "  python3 -m actifix.main process --max-tickets 5",
        "  python3 -m actifix.main stats",
        "",
        "Quarantine Management:",
        "  python3 -m actifix.main quarantine list",
        "  python3 -m actifix.main quarantine view <ticket_id>",
        "",
        "Module Management:",
        "  python3 -m actifix.main modules list",
        "  python3 -m actifix.main modules enable modules.yhatzee",
        "  python3 -m actifix.main modules disable modules.superquiz",
        "",
        "HIGHLIGHT: All operations are ticketed and audited"
    ], 13, 40)
    
    # Page 14: Multi-Agent Workflow
    create_page(doc, "Multi-Agent Development Workflow", [
        "Collaboration Model:",
        "  • Work directly on 'develop' branch",
        "  • No per-change branches required",
        "  • Regular commits and pushes after each ticket",
        "",
        "Isolated State:",
        "  • Each agent uses unique ACTIFIX_DATA_DIR",
        "  • Local database (data/actifix.db) per agent",
        "  • Logs and state isolated",
        "  • Prevents conflicts between agents",
        "",
        "Quick-Start Agent Setup:",
        "  mkdir -p ~/actifix-agent-$(date +%s)/data",
        "  export ACTIFIX_DATA_DIR=~/actifix-agent-$(date +%s)",
        "  export ACTIFIX_CHANGE_ORIGIN=raise_af",
        "  python3 scripts/view_tickets.py",
        "  python3 Do_AF.py 1",
        "",
        "HIGHLIGHT: Agents sync via git pull/push after commits"
    ], 14, 40)
    
    # Page 15: Raise_AF Gate
    create_page(doc, "Raise_AF Change Policy", [
        "Mandatory Rule:",
        "  All code changes must originate from a ticket",
        "  created via actifix.raise_af.record_error()",
        "",
        "Why?",
        "  • Every change is tracked and documented",
        "  • Regressions are visible in ticket system",
        "  • AI assistants have context for improvements",
        "",
        "Enforcement:",
        "  export ACTIFIX_CHANGE_ORIGIN=raise_af",
        "",
        "Create tickets programmatically:",
        "  actifix.record_error(",
        "    message='Description of issue or improvement',",
        "    source='module.py:line',",
        "    error_type='BugFix',",
        "    priority=actifix.TicketPriority.P2,",
        "  )",
        "",
        "WARNING: Changes without tickets are blocked by default"
    ], 15, 40)
    
    # Page 16: AI Integration
    create_page(doc, "AI Integration & Processing", [
        "Multi-Provider Support:",
        "  • Claude Code local auth detection",
        "  • Claude API integration",
        "  • OpenAI GPT-4 Turbo",
        "  • Ollama local model support",
        "  • Free alternative fallbacks",
        "",
        "Automatic Fallback Chain:",
        "  1. Try primary provider",
        "  2. If fails, try next in chain",
        "  3. Log cost tracking for each attempt",
        "  4. Always provide fallback option",
        "",
        "AI Remediation Notes:",
        "  • Generated automatically for each ticket",
        "  • Includes root cause, impact, action",
        "  • Stack trace snippets",
        "  • File context snapshots",
        "  • System state keys",
        "",
        "HIGHLIGHT: 200k token context window management"
    ], 16, 40)
    
    # Page 17: AI Remediation Notes Structure
    create_page(doc, "AI Remediation Notes Format", [
        "Generated Structure:",
        "",
        "Root Cause: <error_type> @ <source>",
        "Impact: ticket <id> (<priority>) requires a code-level fix",
        "Action: Implement the documented robustness improvements",
        "",
        "STACK TRACE:",
        "<truncated stack trace with context>",
        "",
        "FILE CONTEXT SNAPSHOTS:",
        "- <filename>: <relevant code snippets>",
        "",
        "SYSTEM STATE KEYS:",
        "<list of captured system state keys>",
        "",
        "HIGHLIGHT: Structured for AI processing with token limits"
    ], 17, 40)
    
    # Page 18: Module System Overview
    create_page(doc, "Module System Architecture", [
        "Module Types:",
        "  • System modules (built-in)",
        "  • User modules (custom extensions)",
        "",
        "Core Modules:",
        "  • yhatzee - Two-player Yhatzee game",
        "  • superquiz - Multi-player quiz experience",
        "  • pokertool - Poker analysis system",
        "  • dev_assistant - Local Ollama coding assistant",
        "  • artclass - Interactive art teaching",
        "",
        "Module Features:",
        "  • Health checks via /health endpoint",
        "  • Rate limiting (60/min, 600/hour, 2000/day)",
        "  • Access rules (public, local-only, auth-required)",
        "  • Shared ModuleBase helpers",
        "  • Config overrides via ACTIFIX_MODULE_CONFIG_OVERRIDES",
        "",
        "HIGHLIGHT: Modules register in sandbox, failures mark status as error"
    ], 18, 40)
    
    # Page 19: Module Configuration
    create_page(doc, "Module Configuration", [
        "Default Configuration:",
        "  • yhatzee: 127.0.0.1:8090",
        "  • superquiz: 127.0.0.1:8070",
        "",
        "Override via Environment:",
        "  export ACTIFIX_MODULE_CONFIG_OVERRIDES='{",
        '    "yhatzee": {"port": 9101, "host": "127.0.0.2"},',
        '    "superquiz": {"port": 9103}',
        "  }'",
        "",
        "Module Metadata Requirements:",
        "  • name, version, description",
        "  • capabilities (dict)",
        "  • data_access (dict)",
        "  • network (dict)",
        "  • permissions (list)",
        "",
        "Example:",
        "  {",
        '    "name": "modules.yhatzee",',
        '    "version": "1.0.0",',
        '    "capabilities": {"gui": true, "health": true},',
        '    "permissions": ["logging", "fs_read"]',
        "  }",
        "",
        "HIGHLIGHT: Centralized config with environment overrides"
    ], 19, 40)
    
    # Page 20: Security Features
    create_page(doc, "Security Features", [
        "Authentication & Authorization:",
        "  • JWT token validation",
        "  • RBAC enforcement",
        "  • Session management",
        "",
        "Rate Limiting:",
        "  • Token bucket algorithm",
        "  • Per-minute, per-hour, per-day limits",
        "  • Request metrics tracking",
        "",
        "Secrets Management:",
        "  • PBKDF2 password hashing",
        "  • Secure credential storage",
        "  • Secrets scanner (API keys, tokens, credentials)",
        "  • Automatic redaction in logs and tickets",
        "",
        "Ticket Throttling:",
        "  • Priority-aware flood protection",
        "  • Emergency brake for excessive tickets",
        "  • Throttle history persistence",
        "",
        "HIGHLIGHT: Defense-in-depth security approach"
    ], 20, 40)
    
    # Page 21: Secrets Redaction
    create_page(doc, "Automatic Secrets Redaction", [
        "Redacted Patterns:",
        "  • API keys (sk-*, generic patterns)",
        "  • Authorization tokens (Bearer, JWT)",
        "  • AWS credentials (access key, secret key)",
        "  • Passwords in URLs and config",
        "  • Private keys (PEM format)",
        "  • Email addresses (partial)",
        "  • Credit card numbers",
        "  • Social security numbers",
        "  • Generic tokens (long hex strings)",
        "",
        "Example:",
        "  Before: api_key=sk-1234567890abcdef",
        "  After:  api_key=***API_KEY_REDACTED***",
        "",
        "HIGHLIGHT: Applied to logs, tickets, and system state"
    ], 21, 40)
    
    # Page 22: Persistence Layer
    create_page(doc, "Persistence & Durability", [
        "Primary Storage:",
        "  • SQLite database (data/actifix.db)",
        "  • Thread-safe connection pooling",
        "  • Automatic schema migrations",
        "  • WAL mode for concurrency",
        "",
        "Atomic Operations:",
        "  • Atomic file writes",
        "  • Append with size limits",
        "  • Idempotent operations",
        "  • Temporary file pattern",
        "",
        "Fallback Queue:",
        "  • JSON-based queue file",
        "  • Automatic replay on recovery",
        "  • Compact payload format",
        "  • Legacy queue migration",
        "",
        "HIGHLIGHT: No data loss even during database failures"
    ], 22, 40)
    
    # Page 23: Ticket Lifecycle
    create_page(doc, "Ticket Lifecycle", [
        "1. Creation:",
        "  • Error capture or manual recording",
        "  • Context collection (stack, files, system)",
        "  • Duplicate guard generation",
        "  • Priority classification",
        "  • AI notes generation",
        "",
        "2. Storage:",
        "  • Database persistence (data/actifix.db)",
        "  • Fallback queue if DB unavailable",
        "  • Event logging",
        "",
        "3. Processing:",
        "  • DoAF ticket processing",
        "  • AI-assisted remediation",
        "  • Fix validation",
        "  • Status updates",
        "",
        "4. Completion:",
        "  • Evidence collection",
        "  • Quality gate checks",
        "  • Documentation updates",
        "  • Archive/retention policies",
        "",
        "HIGHLIGHT: Full audit trail from creation to completion"
    ], 23, 40)
    
    # Page 24: Quality Gates
    create_page(doc, "Ticket Completion Quality Gates", [
        "Required Fields for Completion:",
        "  • completion_notes (min 20 chars)",
        "  • test_steps (min 10 chars)",
        "  • test_results (min 10 chars)",
        "",
        "Completion Workflow:",
        "  python3 scripts/interactive_ticket_review.py",
        "",
        "Programmatic Completion:",
        "  from actifix.do_af import mark_ticket_complete",
        "  ",
        "  mark_ticket_complete(",
        "    ticket_id='ACT-20260118-XXXXX',",
        "    completion_notes='Added guard in raise_af to clamp payload size.',",
        "    test_steps='Ran python3 test.py --coverage and manual CLI smoke test.',",
        "    test_results='All tests passed; CLI record/health commands succeed.',",
        "  )",
        "",
        "HIGHLIGHT: No ticket can be marked complete without evidence"
    ], 24, 40)
    
    # Page 25: Testing Framework
    create_page(doc, "Testing & Quality Assurance", [
        "Test Commands:",
        "  python3 test.py --coverage",
        "  python3 test.py --fast-coverage",
        "  python3 -m pytest test/ -m 'not slow'",
        "",
        "Architecture Validation:",
        "  python3 -m pytest test/test_architecture_validation.py -v",
        "",
        "System Tests:",
        "  python3 -m actifix.main test",
        "  python3 -m actifix.main health",
        "",
        "Module Testing Harness:",
        "  from actifix.testing import create_module_test_client",
        "  client = create_module_test_client('yhatzee')",
        "  assert client.get('/health').status_code == 200",
        "",
        "Coverage Goals:",
        "  • Full test cycle with Actifix system tests",
        "  • Fast coverage for quick iterations",
        "  • Architecture compliance validation",
        "  • Deterministic testing",
        "",
        "HIGHLIGHT: Quality gates enforced before every commit"
    ], 25, 40)
    
    # Page 26: Use Case - Production API
    create_page(doc, "Use Case: Production API Error Tracking", [
        "Scenario: REST API with database backend",
        "",
        "Implementation:",
        "  1. Enable Actifix capture on startup",
        "  2. Wrap database operations with error handlers",
        "  3. Capture context (request ID, user, endpoint)",
        "  4. Auto-classify priority (P1 for DB errors)",
        "  5. Generate AI remediation notes",
        "  6. Alert team via ticket system",
        "",
        "Benefits:",
        "  • Automatic error deduplication",
        "  • Rich context for debugging",
        "  • AI-assisted remediation",
        "  • Full audit trail",
        "  • Self-healing suggestions",
        "",
        "Example Code:",
        "  try:",
        "    db.execute(query, params)",
        "  except DatabaseError as e:",
        "    record_error(",
        "      message=str(e),",
        "      source=f'{__file__}:{line}',",
        "      run_label='api-db',",
        "      error_type='DatabaseError',",
        "      priority=TicketPriority.P1,",
        "    )",
        "",
        "HIGHLIGHT: Production-ready error management"
    ], 26, 40)
    
    # Page 27: Use Case - CI/CD Pipeline
    create_page(doc, "Use Case: CI/CD Pipeline Monitoring", [
        "Scenario: Track build failures and regressions",
        "",
        "Implementation:",
        "  1. Integrate Actifix in CI scripts",
        "  2. Capture build/test failures",
        "  3. Include git commit context",
        "  4. Auto-classify by failure type",
        "  5. Create tickets for regressions",
        "  6. Track fix progress",
        "",
        "Benefits:",
        "  • Visibility into build health",
        "  • Regression tracking",
        "  • Automated ticket creation",
        "  • AI suggestions for fixes",
        "  • Historical trend analysis",
        "",
        "Example:",
        "  if build_failed():",
        "    record_error(",
        "      message=f'Build failed: {error}',",
        "      source='ci_pipeline.py:1',",
        "      run_label='ci-build',",
        "      error_type='BuildFailure',",
        "      priority=TicketPriority.P2,",
        "    )",
        "",
        "HIGHLIGHT: Self-documenting pipeline failures"
    ], 27, 40)
    
    # Page 28: Use Case - Module Development
    create_page(doc, "Use Case: Module Development & Testing", [
        "Scenario: Developing new Actifix modules",
        "",
        "Implementation:",
        "  1. Use ModuleBase for shared helpers",
        "  2. Register in ModuleRegistry",
        "  3. Implement health endpoint",
        "  4. Add error capture with run_label",
        "  5. Test with module testing harness",
        "  6. Validate architecture compliance",
        "",
        "Benefits:",
        "  • Consistent error handling",
        "  • Automatic health monitoring",
        "  • Sandboxed failure isolation",
        "  • Lifecycle event logging",
        "  • Configurable via environment",
        "",
        "Example:",
        "  from actifix.modules.base import ModuleBase",
        "  ",
        "  class MyModule(ModuleBase):",
        "    def __init__(self):",
        "      super().__init__('my-module')",
        "    ",
        "    def health(self):",
        "      return {'status': 'ok'}",
        "",
        "HIGHLIGHT: Standardized module development"
    ], 28, 40)
    
    # Page 29: Use Case - Multi-Agent Collaboration
    create_page(doc, "Use Case: Multi-Agent Development", [
        "Scenario: Multiple AI agents working on same codebase",
        "",
        "Implementation:",
        "  1. Each agent gets isolated data directory",
        "  2. Work directly on develop branch",
        "  3. Process tickets from shared queue",
        "  4. Commit after each ticket completion",
        "  5. Push and pull to sync with others",
        "  6. No merge conflicts (database is gitignored)",
        "",
        "Benefits:",
        "  • Parallel development",
        "  • No branch management overhead",
        "  • Isolated state prevents conflicts",
        "  • Shared ticket visibility",
        "  • Git-based synchronization",
        "",
        "Setup:",
        "  mkdir -p ~/agent-$(date +%s)/data",
        "  export ACTIFIX_DATA_DIR=~/agent-$(date +%s)",
        "  export ACTIFIX_CHANGE_ORIGIN=raise_af",
        "  python3 scripts/view_tickets.py",
        "",
        "HIGHLIGHT: Scalable collaborative development"
    ], 29, 40)
    
    # Page 30: Use Case - Self-Improving Framework
    create_page(doc, "Use Case: Self-Improving Framework", [
        "Scenario: Actifix tracks and improves itself",
        "",
        "Implementation:",
        "  1. Enable self-development mode",
        "  2. Framework monitors its own behavior",
        "  3. Detects regressions automatically",
        "  4. Creates tickets for framework issues",
        "  5. AI suggests improvements",
        "  6. Track fix progress",
        "",
        "Benefits:",
        "  • Continuous improvement",
        "  • Regression visibility",
        "  • Automated issue detection",
        "  • AI-assisted fixes",
        "  • Quality metrics tracking",
        "",
        "Example:",
        "  actifix.bootstrap_actifix_development()",
        "  ",
        "  # Framework detects its own issue",
        "  actifix.record_error(",
        "    message='Performance regression detected',",
        "    source='actifix/core.py:1',",
        "    error_type='PerformanceRegression',",
        "    priority=actifix.TicketPriority.P2,",
        "  )",
        "",
        "HIGHLIGHT: The framework that improves itself"
    ], 30, 40)
    
    # Page 31: Getting Started - Installation
    create_page(doc, "Getting Started: Installation", [
        "Step 1: Clone Repository",
        "  git clone https://github.com/gmanldn/actifix.git",
        "  cd actifix",
        "",
        "Step 2: Create Virtual Environment",
        "  python3 -m venv .venv",
        "  source .venv/bin/activate",
        "",
        "Step 3: Install Dependencies",
        "  python3 -m pip install -e .",
        "  python3 -m pip install -e '[dev]'  # optional",
        "",
        "Step 4: Start Development Launcher",
        "  python3 scripts/start.py",
        "",
        "Step 5: Run Health Check",
        "  python3 -m actifix.main health",
        "",
        "Step 6: Read Documentation",
        "  docs/INDEX.md",
        "",
        "HIGHLIGHT: Zero-dependency, stdlib-first approach"
    ], 31, 40)
    
    # Page 32: Getting Started - First Error
    create_page(doc, "Getting Started: First Error Capture", [
        "Create a test script:",
        "",
        "File: test_error.py",
        "  import actifix",
        "  ",
        "  actifix.enable_actifix_capture()",
        "  ",
        "  try:",
        "    1 / 0",
        "  except Exception as e:",
        "    actifix.record_error(",
        "      message=str(e),",
        "      source='test_error.py:1',",
        "      run_label='test',",
        "      error_type='ZeroDivisionError',",
        "    )",
        "",
        "Run the script:",
        "  python3 test_error.py",
        "",
        "Check the ticket:",
        "  python3 scripts/view_tickets.py",
        "",
        "HIGHLIGHT: First ticket created in data/actifix.db"
    ], 32, 40)
    
    # Page 33: Getting Started - CLI Exploration
    create_page(doc, "Getting Started: CLI Exploration", [
        "Explore the system:",
        "",
        "View tickets:",
        "  python3 scripts/view_tickets.py",
        "",
        "Check stats:",
        "  python3 -m actifix.main stats",
        "",
        "List modules:",
        "  python3 -m actifix.main modules list",
        "",
        "Enable a module:",
        "  python3 -m actifix.main modules enable modules.yhatzee",
        "",
        "Start the dashboard:",
        "  python3 scripts/start.py",
        "",
        "Access the web UI:",
        "  Open browser to http://localhost:5001",
        "",
        "HIGHLIGHT: Full CLI and web interface available"
    ], 33, 40)
    
    # Page 34: Best Practices - Error Capture
    create_page(doc, "Best Practices: Error Capture", [
        "DO:",
        "  ✓ Enable capture early in application lifecycle",
        "  ✓ Use descriptive run_labels for grouping",
        "  ✓ Capture context for important errors",
        "  ✓ Use appropriate priority levels",
        "  ✓ Include source file and line number",
        "  ✓ Re-raise exceptions when appropriate",
        "",
        "DON'T:",
        "  ✗ Capture every minor warning (use P3/P4)",
        "  ✗ Include sensitive data in messages",
        "  ✗ Skip duplicate checking in production",
        "  ✗ Manually edit the database",
        "  ✗ Create tickets outside Raise_AF gate",
        "",
        "Example:",
        "  GOOD: record_error('DB timeout', 'db.py:42', 'api', 'TimeoutError', P1)",
        "  BAD:  record_error('User clicked wrong button', 'ui.py:100', 'ui', 'UIError', P0)",
        "",
        "HIGHLIGHT: Context matters - capture what's needed for debugging"
    ], 34, 40)
    
    # Page 35: Best Practices - Ticket Management
    create_page(doc, "Best Practices: Ticket Management", [
        "Ticket Creation:",
        "  • Use Raise_AF gate for all changes",
        "  • Set ACTIFIX_CHANGE_ORIGIN=raise_af",
        "  • Create tickets before making changes",
        "  • Include clear, actionable messages",
        "",
        "Ticket Processing:",
        "  • Process highest priority first (P0 → P4)",
        "  • Use DoAF for automated remediation",
        "  • Validate fixes with tests",
        "  • Document completion with evidence",
        "",
        "Ticket Completion:",
        "  • Provide completion_notes (min 20 chars)",
        "  • Document test_steps (min 10 chars)",
        "  • Include test_results (min 10 chars)",
        "  • Use interactive_ticket_review.py",
        "",
        "HIGHLIGHT: Every ticket tells a complete story"
    ], 35, 40)
    
    # Page 36: Best Practices - Multi-Agent
    create_page(doc, "Best Practices: Multi-Agent Workflow", [
        "Agent Setup:",
        "  • Use unique ACTIFIX_DATA_DIR per agent",
        "  • Set ACTIFIX_CHANGE_ORIGIN=raise_af",
        "  • Isolate state to prevent conflicts",
        "",
        "Collaboration:",
        "  • Work directly on develop branch",
        "  • Pull before starting work",
        "  • Commit after each ticket",
        "  • Push regularly to sync",
        "  • No per-change branches needed",
        "",
        "Conflict Prevention:",
        "  • Database is gitignored",
        "  • Each agent has local copy",
        "  • Git handles code conflicts",
        "  • Tickets are shared via git",
        "",
        "HIGHLIGHT: Parallel development without merge conflicts"
    ], 36, 40)
    
    # Page 37: Best Practices - Security
    create_page(doc, "Best Practices: Security", [
        "Secrets Management:",
        "  • Never hardcode secrets in code",
        "  • Use environment variables",
        "  • Actifix auto-redacts in logs/tickets",
        "  • Review redacted output regularly",
        "",
        "Access Control:",
        "  • Use auth-required endpoints for sensitive data",
        "  • Implement rate limiting",
        "  • Validate JWT tokens",
        "  • Enforce RBAC policies",
        "",
        "Data Protection:",
        "  • Encrypt sensitive data at rest",
        "  • Use secure password hashing (PBKDF2)",
        "  • Scan for secrets in code",
        "  • Audit access logs",
        "",
        "HIGHLIGHT: Security is built into every layer"
    ], 37, 40)
    
    # Page 38: Roadmap & Future
    create_page(doc, "Roadmap & Future Development", [
        "Current Focus (v4.x):",
        "  • Ticket processing reliability",
        "  • DoAF remediation automation",
        "  • Operational tooling (dashboards, alerts)",
        "  • AI provider robustness",
        "  • Prompt compression workflows",
        "",
        "Near Future:",
        "  • Enhanced AI integration",
        "  • More module examples",
        "  • Advanced analytics",
        "  • Performance optimizations",
        "  • Community contributions",
        "",
        "Long-term Vision:",
        "  • Fully autonomous remediation",
        "  • Predictive error prevention",
        "  • Cross-project error patterns",
        "  • AI-driven architecture suggestions",
        "  • Self-optimizing framework",
        "",
        "HIGHLIGHT: Continuous evolution with community input"
    ], 38, 40)
    
    # Page 39: Resources & Documentation
    create_page(doc, "Resources & Documentation", [
        "Core Documentation:",
        "  • docs/INDEX.md - Documentation hub",
        "  • docs/QUICKSTART.md - Hands-on setup",
        "  • docs/FRAMEWORK_OVERVIEW.md - Architecture & release notes",
        "  • docs/DEVELOPMENT.md - Workflow & quality gates",
        "",
        "Architecture Docs:",
        "  • docs/architecture/MAP.yaml - Module map",
        "  • docs/architecture/DEPGRAPH.json - Dependency graph",
        "  • docs/architecture/MODULES.md - Module details",
        "",
        "API Documentation:",
        "  • src/actifix/__init__.py - Public API exports",
        "  • src/actifix/api.py - REST API endpoints",
        "  • src/actifix/raise_af.py - Error capture API",
        "",
        "Community & Support:",
        "  • GitHub: https://github.com/gmanldn/actifix",
        "  • Issue tracking",
        "  • Pull requests",
        "  • Discussions",
        "",
        "HIGHLIGHT: Comprehensive documentation for all levels"
    ], 39, 40)
    
    # Page 40: Conclusion
    create_page(doc, "Conclusion", [
        "Actifix provides:",
        "",
        "✓ Zero-dependency error capture",
        "✓ AI-ready tickets with rich context",
        "✓ Self-improving framework capabilities",
        "✓ Durable, atomic persistence",
        "✓ Multi-agent collaborative workflow",
        "✓ Comprehensive security features",
        "✓ Modular extensible architecture",
        "✓ Full audit trail and compliance",
        "",
        "For Developers:",
        "  • Drop-in error management",
        "  • AI-assisted remediation",
        "  • Self-documenting code changes",
        "  • Collaborative development",
        "  • Continuous improvement",
        "",
        "HIGHLIGHT: The framework that tracks and improves itself",
        "",
        "Thank you for your attention!",
        "",
        "Questions?",
        "",
        "Visit: https://github.com/gmanldn/actifix"
    ], 40, 40)
    
    # Save the presentation
    output_file = "Actifix_Developer_Presentation.odp"
    doc.save(output_file)
    
    print(f"✓ Presentation created: {output_file}")
    print(f"✓ Total pages: 40")
    print(f"✓ File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print(f"✓ Created at: {datetime.now().isoformat()}")
    
    return output_file


if __name__ == "__main__":
    print("Creating Actifix Developer Presentation...")
    print("=" * 60)
    
    try:
        output_file = create_presentation()
        print("=" * 60)
        print(f"✓ Successfully created: {output_file}")
        print("\nYou can now open this file with any ODF-compatible presentation viewer:")
        print("  • LibreOffice Impress")
        print("  • OpenOffice Impress")
        print("  • Google Slides (import ODF)")
        print("  • Microsoft PowerPoint (import ODF)")
    except Exception as e:
        print(f"✗ Error creating presentation: {e}")
        import traceback
        traceback.print_exc()