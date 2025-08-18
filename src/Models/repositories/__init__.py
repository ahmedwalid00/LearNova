"""
Repository classes for database operations.

This module contains repository classes that handle CRUD operations
and complex queries for each model using the Repository pattern.
"""

from .base import BaseRepository
from .user_repository import StudentRepository, TeacherRepository, ParentRepository, AdminRepository
from .lesson_repository import LessonRepository, LessonChunkRepository
from .exam_repository import ExamRepository, ExamResultRepository
from .analytics_repository import AnalyticsRepository

__all__ = [
    "BaseRepository",
    "StudentRepository",
    "TeacherRepository", 
    "ParentRepository",
    "AdminRepository",
    "LessonRepository",
    "LessonChunkRepository",
    "ExamRepository",
    "ExamResultRepository",
    "AnalyticsRepository",
]
