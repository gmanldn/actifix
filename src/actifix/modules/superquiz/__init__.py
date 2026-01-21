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
    # Bump version to reflect added features (custom sources, topic/difficulty filters, elimination & dark modes)
    "version": "2.1.0",
    "description": "Multi-player SuperQuiz module with enhanced trivia sources and game modes.",
    "capabilities": {
        "gui": True,
        "health": True,
        "trivia_sources": True,
        "timed_mode": True,
        "custom_questions": True,
        "room_codes": True,
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
    "Music",
    "Movies",
    "Literature",
    "Mythology",
    "Animals",
    # Additional categories for new question sources
    "Numbers",
    "Random Facts",
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
    "Music": 12,
    "Movies": 11,
    "Literature": 10,
    "Mythology": 20,
    "Animals": 27,
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
    "Music": "music",
    "Movies": "film_and_tv",
    "Literature": "arts_and_literature",
    "Mythology": "history",
    "Animals": "science",
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
    "Music": "music",
    "Movies": "film_and_tv",
    "Literature": "arts_and_literature",
    "Mythology": "history",
    "Animals": "science",
}

# New question sources
OPENTRIVIADB_CATEGORY_MAP: Dict[str, int] = {
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
    "Music": 12,
    "Movies": 11,
    "Literature": 10,
    "Mythology": 20,
    "Animals": 27,
}

JSERVICE_CATEGORY_MAP: Dict[str, str] = {
    "General Knowledge": "general_knowledge",
    "Science": "science",
    "History": "history",
    "Geography": "geography",
    "Sports": "sports",
    "Entertainment": "entertainment",
    "Art & Literature": "literature",
    "Technology": "science",
    "Nature": "science",
    "Politics": "politics",
    "Music": "music",
    "Movies": "movies",
    "Literature": "literature",
    "Mythology": "mythology",
    "Animals": "animals",
}

FUNTRIVIA_CATEGORY_MAP: Dict[str, str] = {
    "General Knowledge": "general",
    "Science": "science",
    "History": "history",
    "Geography": "geography",
    "Sports": "sport",
    "Entertainment": "entertainment",
    "Art & Literature": "literature",
    "Technology": "technology",
    "Nature": "nature",
    "Politics": "politics",
    "Music": "music",
    "Movies": "movies",
    "Literature": "literature",
    "Mythology": "mythology",
    "Animals": "animals",
}

QUIZAPI_CATEGORY_MAP: Dict[str, str] = {
    "General Knowledge": "general",
    "Science": "science",
    "History": "history",
    "Geography": "geography",
    "Sports": "sports",
    "Entertainment": "entertainment",
    "Art & Literature": "arts",
    "Technology": "technology",
    "Nature": "nature",
    "Politics": "politics",
    "Music": "music",
    "Movies": "movies",
    "Literature": "literature",
    "Mythology": "mythology",
    "Animals": "animals",
}

USER_AGENT = "Actifix-SuperQuiz/2.1"


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


def _opentriviadb_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
) -> List[Dict[str, object]]:
    """OpenTriviaDB - Alternative OpenTDB endpoint with different question pool."""
    params = [f"amount={amount}", "type=multiple"]
    if difficulty:
        params.append(f"difficulty={difficulty}")
    if category and category != "Random":
        category_id = OPENTRIVIADB_CATEGORY_MAP.get(category)
        if category_id is not None:
            params.append(f"category={category_id}")
    url = f"https://opentriviadb.net/api.php?{'&'.join(params)}"
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
                "source": "OpenTriviaDB",
                "difficulty": item_difficulty if item_difficulty else "unknown",
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _jservice_questions(
    category: Optional[str],
    amount: int,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """JService - Jeopardy-style questions."""
    params = [f"count={amount}"]
    if category and category != "Random":
        slug = JSERVICE_CATEGORY_MAP.get(category)
        if slug:
            params.append(f"category={slug}")
    url = f"https://jservice.io/api/random?{'&'.join(params)}"
    data = _http_get_json(url)
    normalized = []
    for item in data if isinstance(data, list) else []:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            continue
        # JService doesn't provide incorrect answers, generate them
        incorrect = _generate_incorrect_answers(answer)
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", {}).get("title", category or "")),
                "source": "JService",
                "difficulty": "medium",
                "answer": answer,
                "options": _shuffle_options(answer, incorrect),
            }
        )
    return normalized


def _funtrivia_questions(
    category: Optional[str],
    amount: int,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """FunTrivia - Large trivia database."""
    params = [f"limit={amount}"]
    if category and category != "Random":
        slug = FUNTRIVIA_CATEGORY_MAP.get(category)
        if slug:
            params.append(f"category={slug}")
    if topic:
        params.append(f"search={quote(topic)}")
    url = f"https://api.funtrivia.com/questions?{'&'.join(params)}"
    data = _http_get_json(url)
    normalized = []
    for item in data if isinstance(data, list) else []:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correct_answer", "")).strip()
        incorrect = [str(ans).strip() for ans in item.get("incorrect_answers", [])]
        if not question or not correct:
            continue
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", category or "")),
                "source": "FunTrivia",
                "difficulty": "unknown",
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _quizapi_questions(
    category: Optional[str],
    amount: int,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """QuizAPI - Modern trivia API."""
    params = [f"limit={amount}"]
    if category and category != "Random":
        slug = QUIZAPI_CATEGORY_MAP.get(category)
        if slug:
            params.append(f"category={slug}")
    if topic:
        params.append(f"search={quote(topic)}")
    url = f"https://quizapi.io/api/v1/questions?{'&'.join(params)}"
    data = _http_get_json(url)
    normalized = []
    for item in data if isinstance(data, list) else []:
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correct_answer", "")).strip()
        incorrect = [str(ans).strip() for ans in item.get("incorrect_answers", [])]
        if not question or not correct:
            continue
        normalized.append(
            {
                "question": question,
                "category": str(item.get("category", category or "")),
                "source": "QuizAPI",
                "difficulty": str(item.get("difficulty", "unknown")).lower(),
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            }
        )
    return normalized


def _generate_incorrect_answers(correct_answer: str) -> List[str]:
    """Generate plausible incorrect answers when API doesn't provide them."""
    # Simple variations of the correct answer
    variations = [
        correct_answer.upper(),
        correct_answer.lower(),
        correct_answer.replace(" ", "_"),
        correct_answer.split()[0] if " " in correct_answer else correct_answer + " Jr.",
    ]
    # Add some random plausible alternatives
    common_wrong = ["None of the above", "All of the above", "Both A and B", "Not sure"]
    return (variations + common_wrong)[:3]

# ---------------------------------------------------------------------------
# New trivia source implementations
# ---------------------------------------------------------------------------

def _numbers_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Retrieve random numeric trivia facts from the Numbers API.

    Each question asks the player to identify the correct statement among several
    numeric trivia facts. Since the Numbers API only returns a single fact per
    request, this function makes multiple calls to assemble a multiple choice
    question with one correct fact and a few plausible distractors.

    The Numbers API has been documented to provide interesting trivia about
    numbers via endpoints like /random/trivia?json【333602443728674†L99-L115】.
    """
    normalized: List[Dict[str, object]] = []
    for _ in range(max(0, int(amount))):
        try:
            # Correct fact
            data = _http_get_json("http://numbersapi.com/random/trivia?json")
            fact = str(data.get("text", "")).strip()
            if not fact:
                continue
            # Gather incorrect facts
            incorrect: List[str] = []
            attempts = 0
            while len(incorrect) < 3 and attempts < 6:
                attempts += 1
                try:
                    other = _http_get_json("http://numbersapi.com/random/trivia?json")
                    other_fact = str(other.get("text", "")).strip()
                    if other_fact and other_fact != fact and other_fact not in incorrect:
                        incorrect.append(other_fact)
                except Exception:
                    continue
            # If we didn't get enough distractors, pad with generic wrong statements
            while len(incorrect) < 3:
                generic = f"{random.randint(1, 9999)} is the year this quiz was created."
                if generic != fact and generic not in incorrect:
                    incorrect.append(generic)
            normalized.append(
                {
                    "question": "Which of these number facts is true?",
                    "category": "Numbers",
                    "source": "Numbers API",
                    "difficulty": "unknown",
                    "answer": fact,
                    "options": _shuffle_options(fact, incorrect),
                }
            )
        except Exception:
            continue
    return normalized


def _uselessfacts_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Retrieve random useless facts from the Useless Facts API.

    The Useless Facts API provides random trivia facts via GET /api/v2/facts/random【191617076171357†L8-L19】.
    Since these facts are statements without a natural multiple choice structure,
    each question uses the fact itself as a true/false proposition.
    """
    normalized: List[Dict[str, object]] = []
    for _ in range(max(0, int(amount))):
        try:
            data = _http_get_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")
            fact = str(data.get("text", "")).strip()
            if not fact:
                continue
            correct = "True"
            incorrect = ["False", "Maybe", "Unsure"]
            normalized.append(
                {
                    "question": fact,
                    "category": "Random Facts",
                    "source": "Useless Facts API",
                    "difficulty": "easy",
                    "answer": correct,
                    "options": _shuffle_options(correct, incorrect),
                }
            )
        except Exception:
            continue
    return normalized


_LOCAL_QUESTIONS_CACHE: Optional[List[Dict[str, object]]] = None


def _local_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Pull questions from the bundled questions_local.json file.

    This offers an offline fallback for when network sources are unavailable or
    when players prefer a local question set.
    """
    global _LOCAL_QUESTIONS_CACHE
    try:
        # Load and cache local questions
        if _LOCAL_QUESTIONS_CACHE is None:
            local_path = Path(__file__).resolve().parent / "questions_local.json"
            if local_path.exists():
                with open(local_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cache: List[Dict[str, object]] = []
                if isinstance(data, list):
                    for item in data:
                        q = str(item.get("question", "")).strip()
                        a = str(item.get("answer", "")).strip()
                        inc = item.get("incorrect_answers", [])
                        cat = str(item.get("category", "Custom"))
                        diff = str(item.get("difficulty", "unknown")).lower()
                        if not q or not a:
                            continue
                        cache.append(
                            {
                                "question": q,
                                "category": cat,
                                "source": "Local",
                                "difficulty": diff if diff else "unknown",
                                "answer": a,
                                "options": _shuffle_options(a, inc),
                            }
                        )
                _LOCAL_QUESTIONS_CACHE = cache
            else:
                _LOCAL_QUESTIONS_CACHE = []
        pool = _LOCAL_QUESTIONS_CACHE or []
        # Filter by category and difficulty/topic if provided
        filtered = pool
        if category and category != "Random":
            filtered = [q for q in filtered if q.get("category") == category]
        if difficulty:
            temp = [q for q in filtered if q.get("difficulty") == difficulty]
            if temp:
                filtered = temp
        if topic:
            temp = [q for q in filtered if _matches_topic(q, topic)]
            if temp:
                filtered = temp
        random.shuffle(filtered)
        return filtered[:amount]
    except Exception:
        return []


def _gather_questions(
    category: Optional[str],
    amount: int,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
    sources: Optional[Sequence[str]] = None,
) -> List[Dict[str, object]]:
    """
    Gather questions from multiple sources with resilient fallback handling.

    Parameters:
        category: Desired category or None for random.
        amount: Number of questions requested.
        difficulty: Optional difficulty filter.
        topic: Optional search term filter.
        sources: Optional list of source names to include (case-insensitive).
    """
    # Build the full source list with names matching those presented to users.
    all_sources: List[Tuple[str, callable]] = [
        ("OpenTDB", lambda count: _opentdb_questions(category, count, difficulty=difficulty)),
        ("Trivia API", lambda count: _trivia_api_questions(category, count, topic=topic)),
        ("WillFry", lambda count: _willfry_questions(category, count, topic=topic)),
        ("OpenTriviaDB", lambda count: _opentriviadb_questions(category, count, difficulty=difficulty)),
        ("JService", lambda count: _jservice_questions(category, count, topic=topic)),
        ("FunTrivia", lambda count: _funtrivia_questions(category, count, topic=topic)),
        ("QuizAPI", lambda count: _quizapi_questions(category, count, topic=topic)),
        ("Numbers API", lambda count: _numbers_questions(category, count, difficulty=difficulty, topic=topic)),
        ("Useless Facts API", lambda count: _uselessfacts_questions(category, count, difficulty=difficulty, topic=topic)),
        ("Local", lambda count: _local_questions(category, count, difficulty=difficulty, topic=topic)),
    ]
    # Normalise requested sources for comparison
    selected_sources = None
    if sources:
        norm: List[str] = []
        for s in sources:
            s_norm = str(s or "").lower().replace(" ", "").replace("-", "")
            if s_norm:
                norm.append(s_norm)
        selected_sources = set(norm)
    # Filter sources if requested
    active_sources: List[Tuple[str, callable]] = []
    for name, func in all_sources:
        if selected_sources is not None:
            key = name.lower().replace(" ", "").replace("-", "")
            if key not in selected_sources:
                continue
        active_sources.append((name, func))
    if not active_sources:
        active_sources = all_sources
    combined: List[Dict[str, object]] = []
    source_stats: Dict[str, Tuple[int, Optional[str]]] = {}

    # Try each source with resilient fallback
    per_source = max(1, amount // len(active_sources))
    for source_name, source_func in active_sources:
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
        for source_name, source_func in active_sources:
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
    sources: Optional[Sequence[str]] = None,
) -> Tuple[List[Dict[str, object]], bool, bool]:
    """
    Gather snap questions with resilient fallback and filtering.

    Snap mode searches across multiple sources for questions matching a topic
    and/or difficulty. The amount parameter controls how many questions are
    ultimately returned.
    """
    all_sources: List[Tuple[str, callable]] = [
        ("OpenTDB", lambda count: _opentdb_questions(None, count, difficulty=difficulty)),
        ("Trivia API", lambda count: _trivia_api_questions(None, count, topic=topic)),
        ("WillFry", lambda count: _willfry_questions(None, count, topic=topic)),
        ("OpenTriviaDB", lambda count: _opentriviadb_questions(None, count, difficulty=difficulty)),
        ("JService", lambda count: _jservice_questions(None, count, topic=topic)),
        ("FunTrivia", lambda count: _funtrivia_questions(None, count, topic=topic)),
        ("QuizAPI", lambda count: _quizapi_questions(None, count, topic=topic)),
        ("Numbers API", lambda count: _numbers_questions(None, count, difficulty=difficulty, topic=topic)),
        ("Useless Facts API", lambda count: _uselessfacts_questions(None, count, difficulty=difficulty, topic=topic)),
        ("Local", lambda count: _local_questions(None, count, difficulty=difficulty, topic=topic)),
    ]
    selected_sources = None
    if sources:
        norm: List[str] = []
        for s in sources:
            s_norm = str(s or "").lower().replace(" ", "").replace("-", "")
            if s_norm:
                norm.append(s_norm)
        selected_sources = set(norm)
    active_sources: List[Tuple[str, callable]] = []
    for name, func in all_sources:
        if selected_sources is not None:
            key = name.lower().replace(" ", "").replace("-", "")
            if key not in selected_sources:
                continue
        active_sources.append((name, func))
    if not active_sources:
        active_sources = all_sources
    combined: List[Dict[str, object]] = []
    source_stats: Dict[str, Tuple[int, Optional[str]]] = {}

    per_source = max(1, amount // len(active_sources))
    for source_name, source_func in active_sources:
        # Fetch more from snap sources since we apply filtering below
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
        for source_name, source_func in active_sources:
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


def _load_custom_questions(file_path: str) -> List[Dict[str, object]]:
    """Load custom questions from JSON file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        normalized = []
        for item in data:
            question = str(item.get("question", "")).strip()
            correct = str(item.get("answer", "")).strip()
            incorrect = item.get("incorrect_answers", [])
            
            if not question or not correct:
                continue
            
            normalized.append({
                "question": question,
                "category": str(item.get("category", "Custom")),
                "source": "Custom",
                "difficulty": str(item.get("difficulty", "unknown")).lower(),
                "answer": correct,
                "options": _shuffle_options(correct, incorrect),
            })
        
        return normalized
    except Exception as exc:
        record_error(
            message=f"Failed to load custom questions: {exc}",
            source="modules/superquiz/__init__.py:_load_custom_questions",
            error_type="FileLoadError",
            priority=TicketPriority.P2,
        )
        return []


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
                # Additional optional parameters
                raw_difficulty = request.args.get("difficulty")
                difficulty = _normalize_difficulty(raw_difficulty)
                raw_topic = request.args.get("topic")
                topic = _normalize_topic(raw_topic)
                sources_param = request.args.get("sources")
                selected_sources = None
                if sources_param:
                    selected_sources = [s for s in sources_param.split(",") if s.strip()]
                count = request.args.get("count", type=int) or DEFAULT_QUESTIONS_PER_PLAYER
                count = max(1, min(count, 60))
                questions = _gather_questions(
                    category,
                    count,
                    difficulty=difficulty,
                    topic=topic,
                    sources=selected_sources,
                )
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
                sources_param = request.args.get("sources")
                selected_sources = None
                if sources_param:
                    selected_sources = [s for s in sources_param.split(",") if s.strip()]
                count = request.args.get("count", type=int) or DEFAULT_QUESTIONS_PER_PLAYER
                count = max(1, min(count, 60))
                questions, topic_matched, difficulty_matched = _gather_snap_questions(
                    topic,
                    difficulty,
                    count,
                    sources=selected_sources,
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

        @blueprint.route("/api/custom", methods=["POST"])
        def api_custom():
            """Import custom questions from uploaded JSON file."""
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No file provided"}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({"error": "No file selected"}), 400
                
                # Save temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    file.save(f.name)
                    questions = _load_custom_questions(f.name)
                
                return jsonify({
                    "count": len(questions),
                    "questions": questions,
                    "message": f"Loaded {len(questions)} custom questions"
                })
            except Exception as exc:
                helper.record_module_error(
                    message=f"Failed to import custom questions: {exc}",
                    source="modules/superquiz/__init__.py:api_custom",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )
                raise

        @blueprint.route("/api/room", methods=["POST"])
        def api_room():
            """Create or join a multiplayer room."""
            try:
                data = request.get_json() or {}
                action = data.get("action", "create")
                room_code = data.get("room_code")
                
                if action == "create":
                    # Generate a 6-digit room code
                    import random
                    room_code = str(random.randint(100000, 999999))
                    return jsonify({
                        "room_code": room_code,
                        "message": "Room created successfully"
                    })
                elif action == "join":
                    if not room_code:
                        return jsonify({"error": "Room code required"}), 400
                    return jsonify({
                        "room_code": room_code,
                        "message": f"Joined room {room_code}"
                    })
                else:
                    return jsonify({"error": "Invalid action"}), 400
            except Exception as exc:
                helper.record_module_error(
                    message=f"Failed to handle room request: {exc}",
                    source="modules/superquiz/__init__.py:api_room",
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
  <title>SuperQuiz Enhanced</title>
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
      max-width: 1200px;
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
    .panel.delay-3 {
      animation-delay: 0.36s;
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
    input,
    textarea {
      width: 100%;
      padding: 12px 14px;
      font-size: 16px;
      border-radius: 12px;
      border: 1px solid rgba(43, 32, 23, 0.2);
      background: #fff;
      color: var(--ink);
    }
    textarea {
      min-height: 120px;
      font-family: monospace;
      font-size: 14px;
    }
    input:focus,
    select:focus,
    textarea:focus {
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
    .button.tertiary {
      background: linear-gradient(130deg, #6c757d, #adb5bd);
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
    .timer {
      font-size: 24px;
      font-weight: bold;
      color: var(--accent-3);
      text-align: center;
      margin: 10px 0;
    }
    .timer.warning {
      color: #ff9f1c;
    }
    .timer.danger {
      color: #e63946;
      animation: pulse 0.5s infinite;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 16px;
    }
    .stat-card {
      background: rgba(255, 255, 255, 0.7);
      padding: 12px;
      border-radius: 12px;
      text-align: center;
      border: 1px solid rgba(43, 32, 23, 0.15);
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: var(--accent);
    }
    .stat-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
    }
    .room-code {
      font-size: 32px;
      font-weight: bold;
      letter-spacing: 4px;
      text-align: center;
      color: var(--accent);
      margin: 10px 0;
      font-family: "Oswald", sans-serif;
    }
    .source-badge {
      display: inline-block;
      padding: 4px 8px;
      background: rgba(42, 157, 143, 0.2);
      border-radius: 6px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-left: 8px;
    }
    .difficulty-badge {
      display: inline-block;
      padding: 4px 8px;
      background: rgba(247, 127, 0, 0.2);
      border-radius: 6px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-left: 8px;
    }
    @media (max-width: 900px) {
      .title {
        font-size: 42px;
      }
      .play-area.active {
        grid-template-columns: 1fr;
      }
      .stats {
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
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    /* Dark mode variables */
    body.dark {
      --bg: #1a1a1a;
      --panel: #222;
      --ink: #f8f8f8;
      --accent: #ffb703;
      --accent-2: #80ced7;
      --accent-3: #e63946;
      --muted: #a0a0a0;
      --shadow: rgba(0, 0, 0, 0.5);
      --glow: rgba(255, 183, 3, 0.25);
      background: radial-gradient(circle at top, #2c2c2c 0%, #1f1f1f 40%, #161616 100%);
      color: var(--ink);
    }
    /* Eliminated player style */
    .scorecard.eliminated span:first-child {
      text-decoration: line-through;
      opacity: 0.6;
    }
  </style>
</head>
<body>
  <div class="stage">
    <div class="app">
      <header>
        <h1 class="title">SuperQuiz Enhanced</h1>
        <div class="subtitle">10 Sources · Timed & Snap · Custom & Local · Elimination · Dark Mode</div>
        <button id="toggle-dark" class="button tertiary" style="align-self:flex-start; max-width:160px;">Toggle Dark</button>
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
          <label for="questions-count">Questions per Player</label>
          <input id="questions-count" type="number" value="5" min="1" max="20">
          <div class="footer">
            <button class="button tertiary" id="create-room">Create Room</button>
            <button class="button tertiary" id="join-room">Join Room</button>
          </div>
          <div class="room-code hidden" id="room-code-display"></div>
        </section>

        <section class="panel delay-2">
          <h2>Quiz Setup</h2>
          <label for="mode">Mode</label>
          <select id="mode">
            <option value="category" selected>Category Quiz</option>
            <option value="snap">Snap Quiz</option>
            <option value="timed">Timed Mode</option>
            <option value="custom">Custom Questions</option>
            <option value="elimination">Elimination Mode</option>
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
              <option value="Music">Music</option>
              <option value="Movies">Movies</option>
              <option value="Literature">Literature</option>
              <option value="Mythology">Mythology</option>
              <option value="Animals">Animals</option>
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
          
          <div id="timed-fields" class="snap-fields hidden">
            <label for="time-limit">Time per Question (seconds)</label>
            <input id="time-limit" type="number" value="15" min="5" max="60">
            <label for="timed-difficulty">Difficulty</label>
            <select id="timed-difficulty">
              <option value="easy">Easy</option>
              <option value="medium" selected>Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          
          <div id="custom-fields" class="snap-fields hidden">
            <label for="custom-file">Upload JSON Questions</label>
            <input id="custom-file" type="file" accept=".json">
            <label for="custom-json">Or Paste JSON</label>
            <textarea id="custom-json" placeholder='[{"question": "...", "answer": "...", "incorrect_answers": ["...", "..."]}]'></textarea>
          </div>

          <div id="sources-fields" class="snap-fields">
            <label>Question Sources</label>
            <div id="source-options" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:6px;">
              <label><input type="checkbox" value="OpenTDB" checked> OpenTDB</label>
              <label><input type="checkbox" value="Trivia API" checked> Trivia API</label>
              <label><input type="checkbox" value="WillFry" checked> WillFry</label>
              <label><input type="checkbox" value="OpenTriviaDB" checked> OpenTriviaDB</label>
              <label><input type="checkbox" value="JService" checked> JService</label>
              <label><input type="checkbox" value="FunTrivia" checked> FunTrivia</label>
              <label><input type="checkbox" value="QuizAPI" checked> QuizAPI</label>
              <label><input type="checkbox" value="Numbers API" checked> Numbers API</label>
              <label><input type="checkbox" value="Useless Facts API" checked> Useless Facts</label>
              <label><input type="checkbox" value="Local" checked> Local</label>
            </div>
          </div>
          
          <div class="footer">
            <button class="button" id="start">Start Quiz</button>
            <button class="button secondary" id="reset">Reset</button>
          </div>
          <div class="status" id="status"></div>
        </section>

        <section class="panel delay-3">
          <h2>Question Sources</h2>
          <div style="font-size: 13px; line-height: 1.6;">
            <p><strong>10 Sources Active:</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
              <li>OpenTDB</li>
              <li>The Trivia API</li>
              <li>WillFry Trivia</li>
              <li>OpenTriviaDB</li>
              <li>JService (Jeopardy)</li>
              <li>FunTrivia</li>
              <li>QuizAPI</li>
              <li>Numbers API</li>
              <li>Useless Facts API</li>
              <li>Local Questions</li>
            </ul>
            <p style="margin-top: 12px; color: var(--muted);">
              Sources auto-fallback if unavailable. Custom questions supported via JSON upload.
            </p>
          </div>
        </section>
      </div>

      <section class="play-area" id="play-area">
        <div class="panel">
          <div class="meta" id="turn-meta">Player</div>
          <div class="timer hidden" id="timer">15</div>
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
          <div class="stats" id="stats"></div>
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
    const timedFields = document.getElementById("timed-fields");
    const timeLimitEl = document.getElementById("time-limit");
    const timedDifficultyEl = document.getElementById("timed-difficulty");
    const customFields = document.getElementById("custom-fields");
    const customFileEl = document.getElementById("custom-file");
    const customJsonEl = document.getElementById("custom-json");
    const startBtn = document.getElementById("start");
    const resetBtn = document.getElementById("reset");
    const createRoomBtn = document.getElementById("create-room");
    const joinRoomBtn = document.getElementById("join-room");
    const roomCodeDisplay = document.getElementById("room-code-display");
    const statusEl = document.getElementById("status");
    const playArea = document.getElementById("play-area");
    const questionEl = document.getElementById("question");
    const answersEl = document.getElementById("answers");
    const nextBtn = document.getElementById("next");
    const turnMeta = document.getElementById("turn-meta");
    const scoreboardEl = document.getElementById("scoreboard");
    const resultEl = document.getElementById("result");
    const timerEl = document.getElementById("timer");
    const statsEl = document.getElementById("stats");
    const questionsCountEl = document.getElementById("questions-count");
    const sourceOptionsEl = document.getElementById("source-options");
    const darkBtn = document.getElementById("toggle-dark");

    let players = [];
    let questions = [];
    let currentIndex = 0;
    let currentPlayerIndex = 0;
    let answered = false;
    let timerInterval = null;
    let timeRemaining = 0;
    let roomCode = null;
    let stats = {
      correct: 0,
      incorrect: 0,
      total: 0,
      avgTime: 0,
      timeSum: 0
    };
    // Track elimination mode and dynamic questions per player
    let eliminationMode = false;

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
        players.push({ name: "", score: 0, eliminated: false });
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
        if (player.eliminated) {
          row.classList.add("eliminated");
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

    function updateStats() {
      statsEl.innerHTML = "";
      const statsData = [
        { label: "Correct", value: stats.correct },
        { label: "Incorrect", value: stats.incorrect },
        { label: "Avg Time", value: stats.total > 0 ? Math.round(stats.timeSum / stats.total) + "s" : "0s" }
      ];
      
      statsData.forEach(stat => {
        const card = document.createElement("div");
        card.className = "stat-card";
        const value = document.createElement("div");
        value.className = "stat-value";
        value.textContent = stat.value;
        const label = document.createElement("div");
        label.className = "stat-label";
        label.textContent = stat.label;
        card.appendChild(value);
        card.appendChild(label);
        statsEl.appendChild(card);
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
      categoryFields.classList.add("hidden");
      snapFields.classList.add("hidden");
      timedFields.classList.add("hidden");
      customFields.classList.add("hidden");
      
      eliminationMode = (mode === "elimination");
      if (mode === "category" || mode === "elimination") {
        categoryFields.classList.remove("hidden");
      } else if (mode === "snap") {
        snapFields.classList.remove("hidden");
      } else if (mode === "timed") {
        timedFields.classList.remove("hidden");
      } else if (mode === "custom") {
        customFields.classList.remove("hidden");
      }
      showStatus("");
    }

    async function fetchQuestions() {
      const per = Number(questionsCountEl.value) || 5;
      const count = players.length * per;
      const mode = modeEl.value;
      // Collect selected sources
      const sourcesList = Array.from(sourceOptionsEl.querySelectorAll('input:checked')).map(el => el.value);
      const sourcesParam = sourcesList.length > 0 ? `&sources=${encodeURIComponent(sourcesList.join(','))}` : "";
      
      if (mode === "snap") {
        const topic = topicEl.value.trim();
        const difficulty = difficultyEl.value;
        const url = `${basePath()}/api/snap?topic=${encodeURIComponent(topic)}&difficulty=${encodeURIComponent(difficulty)}&count=${count}${sourcesParam}`;
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
      } else if (mode === "timed") {
        const difficulty = timedDifficultyEl.value;
        const url = `${basePath()}/api/snap?difficulty=${encodeURIComponent(difficulty)}&count=${count}${sourcesParam}`;
        try {
          const response = await fetch(url, { cache: "no-store" });
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to load timed questions`);
          }
          const data = await response.json();
          return { questions: data.questions || [], message: "Timed mode active!" };
        } catch (err) {
          console.error("Timed questions fetch error:", err);
          throw new Error(`Timed Quiz API error: ${err.message}`);
        }
      } else if (mode === "custom") {
        const customJson = customJsonEl.value.trim();
        if (customJson) {
          try {
            const parsed = JSON.parse(customJson);
            const questions = Array.isArray(parsed) ? parsed : parsed.questions || [];
            return { questions, message: `Loaded ${questions.length} custom questions` };
          } catch (err) {
            throw new Error(`Invalid JSON: ${err.message}`);
          }
        } else if (customFileEl.files.length > 0) {
          const file = customFileEl.files[0];
          const formData = new FormData();
          formData.append('file', file);
          try {
            const response = await fetch(`${basePath()}/api/custom`, {
              method: 'POST',
              body: formData
            });
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: Failed to upload custom questions`);
            }
            const data = await response.json();
            return { questions: data.questions || [], message: data.message || "" };
          } catch (err) {
            console.error("Custom questions upload error:", err);
            throw new Error(`Custom questions error: ${err.message}`);
          }
        } else {
          throw new Error("Please provide custom questions via JSON or file upload");
        }
      } else {
        const category = categoryEl.value;
        const url = `${basePath()}/api/questions?category=${encodeURIComponent(category)}&count=${count}${sourcesParam}`;
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
    }

    function showStatus(message) {
      statusEl.textContent = message;
    }

    function resetGame() {
      questions = [];
      currentIndex = 0;
      currentPlayerIndex = 0;
      answered = false;
      stats = { correct: 0, incorrect: 0, total: 0, avgTime: 0, timeSum: 0 };
      players.forEach((player) => {
        player.score = 0;
        player.eliminated = false;
      });
      playArea.classList.remove("active");
      questionEl.textContent = "";
      answersEl.innerHTML = "";
      resultEl.textContent = "";
      nextBtn.disabled = true;
      timerEl.classList.add("hidden");
      showStatus("");
      updateScoreboard();
      updateStats();
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
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
      if (modeEl.value === "custom" && !customJsonEl.value.trim() && customFileEl.files.length === 0) {
        showStatus("Provide custom questions via JSON or file upload.");
        return false;
      }
      players.forEach((player, idx) => {
        player.name = names[idx];
      });
      return true;
    }

    function startTimer() {
      const timeLimit = Number(timeLimitEl.value) || 15;
      timeRemaining = timeLimit;
      timerEl.textContent = timeRemaining;
      timerEl.classList.remove("hidden");
      timerEl.classList.remove("warning", "danger");
      
      if (timerInterval) {
        clearInterval(timerInterval);
      }
      
      timerInterval = setInterval(() => {
        timeRemaining--;
        timerEl.textContent = timeRemaining;
        
        if (timeRemaining <= 5) {
          timerEl.classList.add("danger");
        } else if (timeRemaining <= 10) {
          timerEl.classList.add("warning");
        }
        
        if (timeRemaining <= 0) {
          clearInterval(timerInterval);
          timerInterval = null;
          if (!answered) {
            handleTimeout();
          }
        }
      }, 1000);
    }

    function handleTimeout() {
      answered = true;
      nextBtn.disabled = false;
      resultEl.textContent = "Time's up!";
      stats.incorrect++;
      stats.total++;
      updateStats();
      
      const buttons = answersEl.querySelectorAll("button");
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
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
        timerEl.classList.add("hidden");
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
      
      if (modeEl.value === "timed") {
        startTimer();
      } else {
        timerEl.classList.add("hidden");
      }
    }

    function handleAnswer(button, choice, correct) {
      if (answered) {
        return;
      }
      answered = true;
      
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
      
      const buttons = answersEl.querySelectorAll("button");
      buttons.forEach((btn) => {
        if (btn.textContent === correct) {
          btn.classList.add("correct");
        } else if (btn.textContent === choice) {
          btn.classList.add("incorrect");
        }
        btn.disabled = true;
      });
      
      const timeTaken = modeEl.value === "timed" ? (Number(timeLimitEl.value) || 15) - timeRemaining : 0;
      stats.timeSum += timeTaken;
      
      if (choice === correct) {
        if (!players[currentPlayerIndex].eliminated) {
          players[currentPlayerIndex].score += 1;
        }
        resultEl.textContent = "Correct!";
        stats.correct++;
      } else {
        resultEl.textContent = `Incorrect. Answer: ${correct}`;
        stats.incorrect++;
        if (eliminationMode) {
          players[currentPlayerIndex].eliminated = true;
          resultEl.textContent += " Eliminated!";
        }
      }
      stats.total++;
      updateScoreboard();
      updateStats();
      nextBtn.disabled = false;
      // If elimination mode and one or zero players remain, end game early
      if (eliminationMode) {
        const activePlayers = players.filter((p) => !p.eliminated);
        if (activePlayers.length <= 1) {
          nextBtn.disabled = true;
          questionEl.textContent = "";
          answersEl.innerHTML = "";
          timerEl.classList.add("hidden");
          playArea.classList.add("active");
          if (activePlayers.length === 1) {
            showStatus(`Winner: ${activePlayers[0].name || "Player"}!`);
          } else {
            showStatus("No winner - all players eliminated.");
          }
          return;
        }
      }
    }

    function nextQuestion() {
    currentIndex += 1;
      // Advance to the next active player. In elimination mode skip eliminated players.
      if (eliminationMode) {
        let attempts = players.length;
        do {
          currentPlayerIndex = (currentPlayerIndex + 1) % players.length;
          attempts--;
        } while (players[currentPlayerIndex].eliminated && attempts > 0);
      } else {
        currentPlayerIndex = (currentPlayerIndex + 1) % players.length;
      }
      renderQuestion();
    }

    async function startGame() {
      if (!validatePlayers()) {
        return;
      }
      resetGame();
      playArea.classList.add("active");
      showStatus("Gathering questions...");
      eliminationMode = (modeEl.value === "elimination");
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
          const numSources = Array.from(sourceOptionsEl.querySelectorAll('input:checked')).length;
          showStatus(`Loaded ${questions.length} questions from ${numSources} source${numSources !== 1 ? 's' : ''}.`);
        }
        renderQuestion();
      } catch (error) {
        console.error("Game start error:", error);
        showStatus(`Question feed error: ${error.message || "Unknown error"}`);
      }
    }

    async function createRoom() {
      try {
        const response = await fetch(`${basePath()}/api/room`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'create' })
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to create room`);
        }
        const data = await response.json();
        roomCode = data.room_code;
        roomCodeDisplay.textContent = `Room Code: ${roomCode}`;
        roomCodeDisplay.classList.remove("hidden");
        showStatus(`Room created! Share code: ${roomCode}`);
      } catch (err) {
        console.error("Room creation error:", err);
        showStatus(`Room error: ${err.message}`);
      }
    }

    async function joinRoom() {
      const code = prompt("Enter room code:");
      if (!code) return;
      
      try {
        const response = await fetch(`${basePath()}/api/room`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'join', room_code: code })
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to join room`);
        }
        const data = await response.json();
        roomCode = data.room_code;
        roomCodeDisplay.textContent = `Joined Room: ${roomCode}`;
        roomCodeDisplay.classList.remove("hidden");
        showStatus(`Joined room ${roomCode}!`);
      } catch (err) {
        console.error("Room join error:", err);
        showStatus(`Room error: ${err.message}`);
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
    createRoomBtn.addEventListener("click", createRoom);
    joinRoomBtn.addEventListener("click", joinRoom);

    // Toggle dark mode on button click by adding/removing the 'dark' class on the body element
    darkBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark");
    });

    toggleMode();
    buildPlayers();
    resetGame();
  </script>
</body>
</html>
"""