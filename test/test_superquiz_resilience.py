"""Test SuperQuiz resilient fallback handling when external APIs fail."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module
import sys
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from actifix.modules.superquiz import _gather_questions, _local_questions


def test_local_questions_file_exists():
    """Verify that the local questions fallback file exists."""
    module_path = Path(__file__).resolve().parent.parent / "src" / "actifix" / "modules" / "superquiz"
    local_questions_path = module_path / "questions_local.json"

    assert local_questions_path.exists(), "questions_local.json must exist for offline fallback"

    # Verify it contains valid JSON
    with open(local_questions_path, "r") as f:
        questions = json.load(f)

    assert isinstance(questions, list), "Local questions must be a list"
    assert len(questions) > 0, "Local questions file must not be empty"

    # Verify structure of questions
    for q in questions[:5]:  # Check first 5
        assert "question" in q, "Each question must have a 'question' field"
        assert "answer" in q, "Each question must have an 'answer' field"
        assert "category" in q, "Each question must have a 'category' field"


def test_local_questions_returns_data():
    """Test that _local_questions function returns questions."""
    questions = _local_questions(None, 10)

    assert len(questions) > 0, "Should return questions from local file"
    assert len(questions) <= 10, "Should not exceed requested amount"

    # Verify question structure
    for q in questions:
        assert "question" in q
        assert "answer" in q
        assert "category" in q
        assert "source" in q
        assert q["source"] == "Local"


def test_gather_questions_with_all_external_failures():
    """Test that _gather_questions falls back to local questions when all external APIs fail."""

    # Mock all external API functions to raise exceptions
    with patch("actifix.modules.superquiz._opentdb_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._trivia_api_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._willfry_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._opentriviadb_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._jservice_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._funtrivia_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._quizapi_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._trivia_db_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._quizme_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._numbers_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._uselessfacts_questions", side_effect=Exception("API down")):

        # Request 20 questions - should still get some from local fallback
        questions = _gather_questions(None, 20)

        # Should have questions from local fallback
        assert len(questions) > 0, "Should return local questions when all external APIs fail"

        # All questions should be from Local source
        for q in questions:
            assert q.get("source") == "Local", "All questions should be from Local source when external APIs fail"


def test_gather_questions_with_partial_failures():
    """Test that _gather_questions handles partial failures gracefully."""

    # Mock some APIs to fail, others to succeed
    def mock_success(count):
        return [{"question": f"Q{i}", "answer": f"A{i}", "category": "Test", "source": "TestAPI", "difficulty": "easy", "options": ["A", "B", "C", "D"]} for i in range(min(count, 5))]

    with patch("actifix.modules.superquiz._opentdb_questions", side_effect=Exception("API down")), \
         patch("actifix.modules.superquiz._trivia_api_questions", side_effect=mock_success), \
         patch("actifix.modules.superquiz._willfry_questions", side_effect=Exception("API down")):

        questions = _gather_questions(None, 10)

        # Should have some questions from working sources and local fallback
        assert len(questions) > 0, "Should return questions from working sources"


def test_local_questions_with_category_filter():
    """Test that local questions can be filtered by category."""
    science_questions = _local_questions("Science", 5)

    assert len(science_questions) > 0, "Should return science questions"
    for q in science_questions:
        assert q.get("category") == "Science", "All questions should be from Science category"


def test_local_questions_sufficient_quantity():
    """Verify local questions file has enough questions for gameplay."""
    questions = _local_questions(None, 100)  # Request more than available

    # Should have at least 20 questions for a reasonable game
    assert len(questions) >= 20, "Local questions should have at least 20 questions for offline gameplay"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
