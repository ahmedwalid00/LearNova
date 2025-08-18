"""
Models module for LearNova application.

This module provides database models, repositories for CRUD operations,
and services for business logic orchestration.

Repository Pattern:
- BaseRepository: Abstract base class with common CRUD operations
- Specific repositories: Model-specific operations (StudentRepository, etc.)

Service Pattern:
- Service classes orchestrate business logic using multiple repositories
- Handle complex operations and transactions

Usage Example:
    from src.Models.repositories import StudentRepository, LessonRepository
    from src.Models.services import UserService, LessonService
    
    # In your route handlers:
    async def get_student(student_id: UUID, session: AsyncSession):
        student_repo = StudentRepository(session)
        return await student_repo.get_by_id(student_id)
    
    # For complex business logic:
    async def authenticate_user(email: str, password: str, session: AsyncSession):
        user_service = UserService(session)
        return await user_service.authenticate_user(email, password)
"""

# Import repositories
from .repositories import (
    BaseRepository,
    StudentRepository,
    TeacherRepository,
    ParentRepository,
    AdminRepository,
    LessonRepository,
    LessonChunkRepository,
    ExamRepository,
    ExamResultRepository,
    AnalyticsRepository,
)

# Import services
from .services import (
    UserService,
    LessonService,
    ExamService,
)

# Import database models
from .DBSchemes.Schemes import (
    academic_term,
    analytics,
    associations,
    exam_models,
    lesson,
    question_models,
    subject,
    term_week,
    user_models,
)

__all__ = [
    # Repositories
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
    
    # Services
    "UserService",
    "LessonService",
    "ExamService",
    
    # Model modules
    "academic_term",
    "analytics",
    "associations",
    "exam_models",
    "lesson",
    "question_models",
    "subject", 
    "term_week",
    "user_models",
]