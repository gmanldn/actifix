"""SuperQuiz module with a localhost GUI for multi-player quizzes."""

from __future__ import annotations

import html
import json
import random
import ssl
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING, Union
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error

from actifix.modules.base import ModuleBase

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8070,
}
DEFAULT_QUESTIONS_PER_PLAYER = 5
ACCESS_RULE = "local-only"
MODULE_METADATA = {
    "name": "modules.superquiz",
    "version": "1.0.0",
    "description": "Multi-player SuperQuiz module with external trivia sources.",
    "capabilities": {
        "gui": True,
        "health": True,
        "trivia_sources": True,
    },
    "data_access": {
        "state_dir": True,
    },
    "network": {
        "external_requests": True,
    },
    "permissions": ["logging", "fs_read", "network_http"],
}
MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]

CATEGORIES: Tuple[str, ...] = (
    "General Knowledge",
    "Science",
    "History",
    "Geography",
    "Sports",
    "Entertainment",
    "Art & Literature",
    "Technology",
    "Nature",
    "Politics",
)

DIFFICULTIES: Tuple[str, ...] = ("easy", "medium", "hard")

OPENTDB_CATEGORY_MAP: Dict[str, int] = {
    "General Knowledge": 9,
    "Science": 17,
    "History": 23,
    "Geography": 22,
    "Sports": 21,
    "Entertainment": 11,
    "Art & Literature": 25,
    "Technology": 18,
    "Nature": 17,
    "Politics": 24,
}

TRIVIA_API_CATEGORY_MAP: Dict[str, str] = {
    "General Knowledge": "general_knowledge",
    "Science": "science",
    "History": "history",
    "Geography": "geography",
    "Sports": "sport_and_leisure",
    "Entertainment": "film_and_tv",
    "Art & Literature": "arts_and_literature",
    "Technology": "science",
    "Nature": "science",
    "Politics": "society_and_culture",
}

WILLFRY_CATEGORY_MAP: Dict[str, str] = {
    "General Knowledge": "general_knowledge",
    "Science": "science",
    "History": "history",
    "Geography": "geography",
    "Sports": "sport_and_leisure",
    "Entertainment": "film_and_tv",
    "Art & Literature": "arts_and_literature",
    "Technology": "science",
    "Nature": "science",
    "Politics": "society_and_culture",
}

USER_AGENT = "Actifix-SuperQuiz/1.0"


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for SuperQuiz."""
    return ModuleBase(
        module_key="superquiz",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _http_get_json(url: str, timeout: int = 8) -> object:
    """Fetch JSON from URL with SSL certificate verification disabled for resilience."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        # Create SSL context that doesn't verify certificates (for resilience)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        with urlopen(request, timeout=timeout, context=ssl_context) as response:
            payload = response.read()
        return json.loads(payload.decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        # Log but don't raise - let caller handle fallback
        raise URLError(f"Failed to fetch from {url}: {exc}") from exc


def _shuffle_options(correct: str, incorrect: Sequence[str]) -> List[str]:
    options = list(incorrect) + [correct]
    random.shuffle(options)
    return options


def _normalize_category(category: Optional[str]) -> Optional[str]:
    if category is None:
        return None
    category = category.strip()
    if not category:
        return None
    if category.lower() == "random":
        return "Random"
    for name in CATEGORIES:
        if name.lower() == category.lower():
            return name
    return None


def _normalize_difficulty(difficulty: Optional[str]) -> Optional[str]:
    if difficulty is None:
        return None
    difficulty = difficulty.strip().lower()
    if difficulty in DIFFICULTIES:
        return difficulty
    return None


def _normalize_topic(topic: Optional[str]) -> Optional[str]:
    if topic is None:
        return None
    topic = topic.strip()
    if not topic:
        return None
    return topic


def _matches_topic(question: Dict[str, object], topic: str) -> bool:
    target = topic.lower()
    haystack = f"{question.get('question', '')} {question.get('category', '')}"
    return target in str(haystack).lower()


def _apply_topic_filter(
    questions: Sequence[Dict[str, object]],
    topic: Optional[str],
) -> Tuple[List[Dict[str, object]], bool]:
    if not topic:
        return list(questions), True
    matched = [question for question in questions if _matches_topic(question, topic)]
    if matched:
        return matched, True
    return list(questions), False


def _apply_difficulty_filter(
    questions: Sequence[Dict[str, object]],
    difficulty: Optional[str],
    amount: int,
) -> Tuple[List[Dict[str, object]], bool]:
    if not difficulty:
        return list(questions), True
    matching = [q for q in questions if q.get("difficulty") == difficulty]
    unknown = [
        q
        for q in questions
        if q.get("difficulty") in (None, "", "unknown")
    ]
    selected = matching[:amount]
    if len(selected) < amount:
        selected.extend(unknown[: max(0, amount - len(selected))])
    if selected:
        return selected, bool(matching)
    return list(questions)[:amount], False


def _opentdb_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
) -> List[Dict[str, object]]:
    params = [f"amount={amount}", "type=multiple"]
    if difficulty:
        params.append(f"difficulty={difficulty}")
    if category and category != "Random":
        category_id = OPENTDB_CATEGORY_MAP.get(category)
        if category_id is not None:
            params.append(f"category={category_id}")
    url = f"https://opentdb.com/api.php?{'&'.join(params)}"
    data = _http_get_json(url)
    results = data.get("results", []) if isinstance(data, dict) else []
    normalized = []
    for item in results:
        question = html.unescape(str(item.get("question", ""))).strip()
        correct = html.unescape(str(item.get("correct_answer", ""))).strip()
        incorrect = [html.unescape(str(ans)).strip() for ans in item.get("incorrect_answers", [])]
        item_difficulty = str(item.get("difficulty", difficulty or "unknown")).lower()
        if not question or not correct:
            continue
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", category or "")),
                "source": "OpenTDB",
                "difficulty": item_difficulty if item_difficulty else "unknown",
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _trivia_api_questions(
    category: Optional[str],
    amount: int,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    params = [f"limit={amount}"]
    if category and category != "Random":
        slug = TRIVIA_API_CATEGORY_MAP.get(category)
        if slug:
            params.append(f"categories={slug}")
    if topic:
        params.append(f"search={quote(topic)}")
    url = f"https://the-trivia-api.com/api/questions?{'&'.join(params)}"
    data = _http_get_json(url)
    normalized = []
    for item in data if isinstance(data, list) else []:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correctAnswer", "")).strip()
        incorrect = [str(ans).strip() for ans in item.get("incorrectAnswers", [])]
        item_difficulty = str(item.get("difficulty", "unknown")).lower()
        if not question or not correct:
            continue
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", category or "")),
                "source": "The Trivia API",
                "difficulty": item_difficulty if item_difficulty else "unknown",
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _willfry_questions(
    category: Optional[str],
    amount: int,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    params = [f"limit={amount}"]
    if category and category != "Random":
        slug = WILLFRY_CATEGORY_MAP.get(category)
        if slug:
            params.append(f"categories={slug}")
    url = f"https://api.trivia.willfry.co.uk/questions?{'&'.join(params)}"
    data = _http_get_json(url)
    normalized = []
    for item in data if isinstance(data, list) else []:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correctAnswer", "")).strip()
        incorrect = [str(ans).strip() for ans in item.get("incorrectAnswers", [])]
        if not question or not correct:
            continue
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", category or "")),
                "source": "WillFry Trivia",
                "difficulty": "unknown",
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _gather_questions(category: Optional[str], amount: int) -> List[Dict[str, object]]:
    """Gather questions from multiple sources with resilient fallback handling."""
    sources = [
        ("OpenTDB", lambda count: _opentdb_questions(category, count)),
        ("Trivia API", lambda count: _trivia_api_questions(category, count)),
        ("WillFry", lambda count: _willfry_questions(category, count)),
    ]
    combined: List[Dict[str, object]] = []
    source_stats: Dict[str, Tuple[int, Optional[str]]] = {}
    
    # Try each source with resilient fallback
    per_source = max(1, amount // len(sources))
    for source_name, source_func in sources:
        try:
            fetched = source_func(per_source)
            combined.extend(fetched)
            source_stats[source_name] = (len(fetched), None)
        except Exception as exc:
            source_stats[source_name] = (0, str(exc))
            # Silently continue to next source
    
    # If we don't have enough questions, try to fetch more from working sources
    if len(combined) < amount:
        shortage = amount - len(combined)
        for source_name, source_func in sources:
            if len(combined) >= amount:
                break
            try:
                fetched = source_func(shortage)
                combined.extend(fetched)
            except Exception:
                # Already tracked failure, continue
                pass
    
    # Log quality metric if any sources failed
    if any(err for _, (_, err) in source_stats.items() if err):
        failed_sources = [name for name, (_, err) in source_stats.items() if err]
        record_error(
            message=f"Some question sources failed during gather: {', '.join(failed_sources)}. Served {len(combined)} questions from working sources.",
            source="modules/superquiz/__init__.py:_gather_questions",
            error_type="PartialFailure",
            priority=TicketPriority.P2,
        )
    
    random.shuffle(combined)
    return combined[:amount]


def _gather_snap_questions(
    topic: Optional[str],
    difficulty: Optional[str],
    amount: int,
) -> Tuple[List[Dict[str, object]], bool, bool]:
    """Gather snap questions with resilient fallback and filtering."""
    sources = [
        ("OpenTDB", lambda count: _opentdb_questions(None, count, difficulty=difficulty)),
        ("Trivia API", lambda count: _trivia_api_questions(None, count, topic=topic)),
        ("WillFry", lambda count: _willfry_questions(None, count, topic=topic)),
    ]
    combined: List[Dict[str, object]] = []
    source_stats: Dict[str, Tuple[int, Optional[str]]] = {}
    
    per_source = max(1, amount // len(sources))
    for source_name, source_func in sources:
        fetch_count = min(max(per_source * 3, per_source + 2), 20)
        try:
            fetched = source_func(fetch_count)
            combined.extend(fetched)
            source_stats[source_name] = (len(fetched), None)
        except Exception as exc:
            source_stats[source_name] = (0, str(exc))
            # Silently continue to next source
    
    # If we don't have enough questions, try to fetch more from working sources
    if len(combined) < amount * 2:
        shortage = (amount * 2) - len(combined)
        for source_name, source_func in sources:
            if len(combined) >= amount * 2:
                break
            try:
                fetched = source_func(shortage)
                combined.extend(fetched)
            except Exception:
                pass
    
    # Log quality metric if any sources failed
    if any(err for _, (_, err) in source_stats.items() if err):
        failed_sources = [name for name, (_, err) in source_stats.items() if err]
        record_error(
            message=f"Some snap question sources failed: {', '.join(failed_sources)}. Served {len(combined)} questions with filters from working sources.",
            source="modules/superquiz/__init__.py:_gather_snap_questions",
            error_type="PartialFailure",
            priority=TicketPriority.P2,
        )
    
    random.shuffle(combined)
    filtered, topic_matched = _apply_topic_filter(combined, topic)
    filtered, difficulty_matched = _apply_difficulty_filter(filtered, difficulty, amount)
    return filtered[:amount], topic_matched, difficulty_matched


def _scoreboard(players: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return [
        {"name": str(player["name"]), "score": int(player["score"])}
        for player in players
    ]


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/superquiz",
) -> Blueprint:
    """Create the Flask blueprint that serves the SuperQuiz GUI."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response, jsonify, request

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("superquiz", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            return Response(_HTML_PAGE, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        @blueprint.route("/api/questions", methods=["GET"])
        def api_questions():
            try:
                raw_category = request.args.get("category")
                category = _normalize_category(raw_category)
                count = request.args.get("count", type=int) or DEFAULT_QUESTIONS_PER_PLAYER
                count = max(1, min(count, 60))
                questions = _gather_questions(category, count)
                return jsonify(
                    {
                        "category": category or "Random",
                        "count": len(questions),
                        "questions": questions,
                    }
                )
            except Exception as exc:
                helper.record_module_error(
                    message=f"Failed to fetch SuperQuiz questions: {exc}",
                    source="modules/superquiz/__init__.py:api_questions",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )
                raise

        @blueprint.route("/api/snap", methods=["GET"])
        def api_snap():
            try:
                raw_topic = request.args.get("topic")
                raw_difficulty = request.args.get("difficulty")
                topic = _normalize_topic(raw_topic)
                difficulty = _normalize_difficulty(raw_difficulty)
                count = request.args.get("count", type=int) or DEFAULT_QUESTIONS_PER_PLAYER
                count = max(1, min(count, 60))
                questions, topic_matched, difficulty_matched = _gather_snap_questions(
                    topic,
                    difficulty,
                    count,
                )
                return jsonify(
                    {
                        "topic": topic or "",
                        "difficulty": difficulty or "",
                        "count": len(questions),
                        "topic_matched": topic_matched,
                        "difficulty_matched": difficulty_matched,
                        "questions": questions,
                    }
                )
            except Exception as exc:
                helper.record_module_error(
                    message=f"Failed to fetch SuperQuiz snap questions: {exc}",
                    source="modules/superquiz/__init__.py:api_snap",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )
                raise

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create SuperQuiz blueprint: {exc}",
            source="modules/superquiz/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create the Flask app that serves the SuperQuiz GUI."""
    try:
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create SuperQuiz GUI app: {exc}",
            source="modules/superquiz/__init__.py:create_app",
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
    """Run the SuperQuiz GUI on localhost."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "SUPERQUIZ_GUI_START",
            f"SuperQuiz GUI running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": "modules.superquiz"},
            source="modules.superquiz.run_gui",
        )
        app.run(host=resolved_host, port=resolved_port, debug=debug)
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start SuperQuiz GUI: {exc}",
            source="modules/superquiz/__init__.py:run_gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SuperQuiz Module</title>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Oswald:wght@300;500;700&family=Crimson+Text:wght@400;600&display=swap");
    :root {
      color-scheme: light;
      --bg: #f7f1e1;
      --panel: #fff7e0;
      --ink: #2b2017;
      --accent: #f77f00;
      --accent-2: #2a9d8f;
      --accent-3: #e63946;
      --muted: #6b5b4b;
      --shadow: rgba(33, 21, 11, 0.15);
      --glow: rgba(247, 127, 0, 0.25);
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: "Crimson Text", "Times New Roman", serif;
      background: radial-gradient(circle at top, #fff5dc 0%, #f6e7c3 40%, #ecd7a5 100%);
      color: var(--ink);
      min-height: 100vh;
    }
    .stage {
      position: relative;
      overflow: hidden;
      min-height: 100vh;
      padding-bottom: 80px;
    }
    .stage::before,
    .stage::after {
      content: "";
      position: absolute;
      border-radius: 999px;
      filter: blur(0);
      opacity: 0.6;
      z-index: 0;
    }
    .stage::before {
      width: 320px;
      height: 320px;
      background: radial-gradient(circle at 30% 30%, #ffe8b0 0%, transparent 70%);
      top: -100px;
      right: -120px;
    }
    .stage::after {
      width: 240px;
      height: 240px;
      background: radial-gradient(circle at 70% 70%, #c1f0e6 0%, transparent 70%);
      bottom: -80px;
      left: -60px;
    }
    .app {
      position: relative;
      z-index: 1;
      max-width: 1100px;
      margin: 0 auto;
      padding: 48px 24px 32px;
      animation: fadeIn 0.9s ease forwards;
    }
    header {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .title {
      font-family: "Oswald", "Arial Narrow", sans-serif;
      font-size: 56px;
      text-transform: uppercase;
      letter-spacing: 4px;
      margin: 0;
    }
    .subtitle {
      text-transform: uppercase;
      letter-spacing: 3px;
      font-size: 12px;
      color: var(--muted);
      font-family: "Oswald", sans-serif;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 22px;
      margin-top: 32px;
    }
    .panel {
      background: var(--panel);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 16px 30px var(--shadow);
      border: 1px solid rgba(43, 32, 23, 0.08);
      transform: translateY(10px);
      opacity: 0;
      animation: panelUp 0.8s ease forwards;
    }
    .panel.delay-1 {
      animation-delay: 0.12s;
    }
    .panel.delay-2 {
      animation-delay: 0.24s;
    }
    .panel h2 {
      font-family: "Oswald", sans-serif;
      font-size: 20px;
      margin-top: 0;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    label {
      display: block;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 8px;
      font-family: "Oswald", sans-serif;
    }
    select,
    input {
      width: 100%;
      padding: 12px 14px;
      font-size: 16px;
      border-radius: 12px;
      border: 1px solid rgba(43, 32, 23, 0.2);
      background: #fff;
      color: var(--ink);
    }
    input:focus,
    select:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--glow);
    }
    .button {
      border: none;
      background: linear-gradient(130deg, var(--accent), #ffb703);
      color: #20120b;
      font-family: "Oswald", sans-serif;
      letter-spacing: 1px;
      text-transform: uppercase;
      padding: 12px 18px;
      border-radius: 999px;
      cursor: pointer;
      font-size: 14px;
      box-shadow: 0 10px 18px rgba(247, 127, 0, 0.3);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .button.secondary {
      background: linear-gradient(130deg, var(--accent-2), #9ae6b4);
    }
    .button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
      box-shadow: none;
    }
    .button:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 12px 22px rgba(247, 127, 0, 0.35);
    }
    .players {
      display: grid;
      gap: 12px;
    }
    .players input {
      font-size: 15px;
    }
    .hidden {
      display: none;
    }
    .snap-fields {
      display: grid;
      gap: 12px;
      margin-top: 16px;
    }
    .play-area {
      display: none;
      margin-top: 30px;
      gap: 20px;
    }
    .play-area.active {
      display: grid;
      grid-template-columns: 2fr 1fr;
    }
    .question {
      font-size: 26px;
      line-height: 1.3;
      margin: 12px 0 18px;
    }
    .meta {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: var(--muted);
      margin-bottom: 10px;
      font-family: "Oswald", sans-serif;
    }
    .answers {
      display: grid;
      gap: 12px;
    }
    .answer {
      padding: 12px 14px;
      border-radius: 14px;
      border: 2px solid transparent;
      background: #fff;
      cursor: pointer;
      font-size: 16px;
      text-align: left;
      transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .answer:hover {
      transform: translateY(-2px);
      border-color: var(--accent);
    }
    .answer.correct {
      border-color: var(--accent-2);
      background: rgba(42, 157, 143, 0.15);
    }
    .answer.incorrect {
      border-color: var(--accent-3);
      background: rgba(230, 57, 70, 0.12);
    }
    .scoreboard {
      display: grid;
      gap: 10px;
    }
    .scorecard {
      display: flex;
      justify-content: space-between;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(43, 32, 23, 0.15);
    }
    .active-player {
      font-weight: 600;
      color: var(--accent-3);
    }
    .footer {
      margin-top: 28px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .status {
      font-size: 14px;
      color: var(--muted);
      min-height: 20px;
    }
    .result {
      margin-top: 16px;
      font-size: 18px;
    }
    @media (max-width: 900px) {
      .title {
        font-size: 42px;
      }
      .play-area.active {
        grid-template-columns: 1fr;
      }
    }
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    @keyframes panelUp {
      from {
        opacity: 0;
        transform: translateY(18px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>
</head>
<body>
  <div class="stage">
    <div class="app">
      <header>
        <h1 class="title">SuperQuiz</h1>
        <div class="subtitle">Fast rounds. Loud knowledge. 1 to 6 players.</div>
      </header>

      <div class="grid">
        <section class="panel delay-1">
          <h2>Set the Stage</h2>
          <label for="player-count">Players</label>
          <select id="player-count">
            <option value="1">1 Player</option>
            <option value="2" selected>2 Players</option>
            <option value="3">3 Players</option>
            <option value="4">4 Players</option>
            <option value="5">5 Players</option>
            <option value="6">6 Players</option>
          </select>
          <div class="players" id="players"></div>
        </section>

        <section class="panel delay-2">
          <h2>Quiz Setup</h2>
          <label for="mode">Mode</label>
          <select id="mode">
            <option value="category" selected>Category Quiz</option>
            <option value="snap">Snap Quiz</option>
          </select>
          <div id="category-fields">
            <label for="category">Category</label>
            <select id="category">
              <option value="Random">Random</option>
              <option value="General Knowledge">General Knowledge</option>
              <option value="Science">Science</option>
              <option value="History">History</option>
              <option value="Geography">Geography</option>
              <option value="Sports">Sports</option>
              <option value="Entertainment">Entertainment</option>
              <option value="Art & Literature">Art & Literature</option>
              <option value="Technology">Technology</option>
              <option value="Nature">Nature</option>
              <option value="Politics">Politics</option>
            </select>
          </div>
          <div id="snap-fields" class="snap-fields hidden">
            <label for="topic">Topic</label>
            <input id="topic" type="text" placeholder="e.g. Space, Jazz, Ocean life">
            <label for="difficulty">Difficulty</label>
            <select id="difficulty">
              <option value="easy">Easy</option>
              <option value="medium" selected>Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div class="footer">
            <button class="button" id="start">Start Quiz</button>
            <button class="button secondary" id="reset">Reset</button>
          </div>
          <div class="status" id="status"></div>
        </section>
      </div>

      <section class="play-area" id="play-area">
        <div class="panel">
          <div class="meta" id="turn-meta">Player</div>
          <div class="question" id="question">Loading question...</div>
          <div class="answers" id="answers"></div>
          <div class="result" id="result"></div>
          <div class="footer">
            <button class="button" id="next" disabled>Next Question</button>
          </div>
        </div>
        <div class="panel">
          <h2>Scoreboard</h2>
          <div class="scoreboard" id="scoreboard"></div>
        </div>
      </section>
    </div>
  </div>

  <script>
    const playerCountEl = document.getElementById("player-count");
    const playersEl = document.getElementById("players");
    const modeEl = document.getElementById("mode");
    const categoryFields = document.getElementById("category-fields");
    const categoryEl = document.getElementById("category");
    const snapFields = document.getElementById("snap-fields");
    const topicEl = document.getElementById("topic");
    const difficultyEl = document.getElementById("difficulty");
    const startBtn = document.getElementById("start");
    const resetBtn = document.getElementById("reset");
    const statusEl = document.getElementById("status");
    const playArea = document.getElementById("play-area");
    const questionEl = document.getElementById("question");
    const answersEl = document.getElementById("answers");
    const nextBtn = document.getElementById("next");
    const turnMeta = document.getElementById("turn-meta");
    const scoreboardEl = document.getElementById("scoreboard");
    const resultEl = document.getElementById("result");

    let players = [];
    let questions = [];
    let currentIndex = 0;
    let currentPlayerIndex = 0;
    let answered = false;

    const QUESTIONS_PER_PLAYER = 5;

    function renderPlayerInputs(count) {
      playersEl.innerHTML = "";
      for (let i = 0; i < count; i += 1) {
        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = `Player ${i + 1} name`;
        input.value = players[i] ? players[i].name : "";
        input.dataset.index = String(i);
        input.addEventListener("input", (event) => {
          const idx = Number(event.target.dataset.index);
          if (!Number.isNaN(idx) && players[idx]) {
            players[idx].name = event.target.value;
          }
        });
        playersEl.appendChild(input);
      }
    }

    function buildPlayers() {
      const count = Number(playerCountEl.value);
      players = [];
      for (let i = 0; i < count; i += 1) {
        players.push({ name: "", score: 0 });
      }
      renderPlayerInputs(count);
    }

    function updateScoreboard() {
      scoreboardEl.innerHTML = "";
      players.forEach((player, index) => {
        const row = document.createElement("div");
        row.className = "scorecard";
        if (index === currentPlayerIndex) {
          row.classList.add("active-player");
        }
        const name = document.createElement("span");
        name.textContent = player.name || `Player ${index + 1}`;
        const score = document.createElement("span");
        score.textContent = String(player.score);
        row.appendChild(name);
        row.appendChild(score);
        scoreboardEl.appendChild(row);
      });
    }

    function basePath() {
      if (window.location.pathname.includes("/modules/superquiz")) {
        return "/modules/superquiz";
      }
      return "";
    }

    function toggleMode() {
      const mode = modeEl.value;
      if (mode === "snap") {
        categoryFields.classList.add("hidden");
        snapFields.classList.remove("hidden");
      } else {
        categoryFields.classList.remove("hidden");
        snapFields.classList.add("hidden");
      }
      showStatus("");
    }

    async function fetchQuestions() {
      const count = players.length * QUESTIONS_PER_PLAYER;
      if (modeEl.value === "snap") {
        const topic = topicEl.value.trim();
        const difficulty = difficultyEl.value;
        const url = `${basePath()}/api/snap?topic=${encodeURIComponent(topic)}&difficulty=${encodeURIComponent(difficulty)}&count=${count}`;
        try {
          const response = await fetch(url, { cache: "no-store" });
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to load snap questions`);
          }
          const data = await response.json();
          let message = "";
          if (!data.topic_matched) {
            message = "Topic matches were limited, expanded to related questions.";
          } else if (!data.difficulty_matched) {
            message = "Difficulty matches were limited, mixed in more questions.";
          }
          return { questions: data.questions || [], message };
        } catch (err) {
          console.error("Snap questions fetch error:", err);
          throw new Error(`Snap Quiz API error: ${err.message}. Ensure the API server is running on port 5001.`);
        }
      }
      const category = categoryEl.value;
      const url = `${basePath()}/api/questions?category=${encodeURIComponent(category)}&count=${count}`;
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to load questions`);
        }
        const data = await response.json();
        return { questions: data.questions || [], message: "" };
      } catch (err) {
        console.error("Questions fetch error:", err);
        throw new Error(`Question API error: ${err.message}. Ensure the API server is running on port 5001.`);
      }
    }

    function showStatus(message) {
      statusEl.textContent = message;
    }

    function resetGame() {
      questions = [];
      currentIndex = 0;
      currentPlayerIndex = 0;
      answered = false;
      players.forEach((player) => {
        player.score = 0;
      });
      playArea.classList.remove("active");
      questionEl.textContent = "";
      answersEl.innerHTML = "";
      resultEl.textContent = "";
      nextBtn.disabled = true;
      showStatus("");
      updateScoreboard();
    }

    function validatePlayers() {
      const names = Array.from(playersEl.querySelectorAll("input")).map((input) => input.value.trim());
      if (names.some((name) => !name)) {
        showStatus("Add a name for every player.");
        return false;
      }
      if (modeEl.value === "snap" && !topicEl.value.trim()) {
        showStatus("Add a topic for Snap Quiz mode.");
        return false;
      }
      players.forEach((player, idx) => {
        player.name = names[idx];
      });
      return true;
    }

    function renderQuestion() {
      if (!questions.length) {
        showStatus("No questions available. Try another category.");
        return;
      }
      if (currentIndex >= questions.length) {
        showStatus("Quiz complete! Final scores locked in.");
        questionEl.textContent = "Quiz complete.";
        answersEl.innerHTML = "";
        resultEl.textContent = "";
        nextBtn.disabled = true;
        return;
      }
      answered = false;
      nextBtn.disabled = true;
      resultEl.textContent = "";
      const question = questions[currentIndex];
      const player = players[currentPlayerIndex];
      const sourceText = question.source ? ` | ${question.source}` : "";
      const difficultyText = question.difficulty ? ` | ${question.difficulty}` : "";
      turnMeta.textContent = `Round ${currentIndex + 1} | ${player.name}${sourceText}${difficultyText}`;
      questionEl.textContent = question.question;
      answersEl.innerHTML = "";
      const options = question.options || [];
      options.forEach((option) => {
        const btn = document.createElement("button");
        btn.className = "answer";
        btn.textContent = option;
        btn.addEventListener("click", () => handleAnswer(btn, option, question.answer));
        answersEl.appendChild(btn);
      });
      updateScoreboard();
    }

    function handleAnswer(button, choice, correct) {
      if (answered) {
        return;
      }
      answered = true;
      const buttons = answersEl.querySelectorAll("button");
      buttons.forEach((btn) => {
        if (btn.textContent === correct) {
          btn.classList.add("correct");
        } else if (btn.textContent === choice) {
          btn.classList.add("incorrect");
        }
        btn.disabled = true;
      });
      if (choice === correct) {
        players[currentPlayerIndex].score += 1;
        resultEl.textContent = "Correct!";
      } else {
        resultEl.textContent = `Incorrect. Answer: ${correct}`;
      }
      updateScoreboard();
      nextBtn.disabled = false;
    }

    function nextQuestion() {
      currentIndex += 1;
      currentPlayerIndex = (currentPlayerIndex + 1) % players.length;
      renderQuestion();
    }

    async function startGame() {
      if (!validatePlayers()) {
        return;
      }
      resetGame();
      playArea.classList.add("active");
      showStatus("Gathering questions...");
      try {
        const result = await fetchQuestions();
        questions = result.questions;
        if (!questions.length) {
          showStatus("No questions returned. Try another category.");
          return;
        }
        if (result.message) {
          showStatus(result.message);
        } else {
          showStatus(`Loaded ${questions.length} questions.`);
        }
        renderQuestion();
      } catch (error) {
        console.error("Game start error:", error);
        showStatus(`Question feed error: ${error.message || "Unknown error"}`);
      }
    }

    playerCountEl.addEventListener("change", () => {
      buildPlayers();
    });
    modeEl.addEventListener("change", toggleMode);
    startBtn.addEventListener("click", startGame);
    resetBtn.addEventListener("click", () => {
      buildPlayers();
      resetGame();
    });
    nextBtn.addEventListener("click", nextQuestion);

    toggleMode();
    buildPlayers();
    resetGame();
  </script>
</body>
</html>
"""