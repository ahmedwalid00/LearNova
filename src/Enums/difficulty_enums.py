"""
Difficulty level enumerations for questions and exams.
"""

from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions and exams."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
