"""
Usage examples for the repository and service patterns.

This file demonstrates how to use the repository and service classes
in your FastAPI route handlers and business logic.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

# Example usage in FastAPI route handlers
from src.Models.repositories import StudentRepository, LessonRepository
from src.Models.services import UserService, LessonService, ExamService


# Example 1: Using repositories directly
async def get_student_by_id(student_id: UUID, session: AsyncSession):
    """Example of using repository directly for simple CRUD operations."""
    student_repo = StudentRepository(session)
    return await student_repo.get_by_id(student_id)


async def get_students_by_rating(min_rating: float, max_rating: float, session: AsyncSession):
    """Example of using repository-specific method."""
    student_repo = StudentRepository(session)
    return await student_repo.get_by_rating_range(min_rating, max_rating)


# Example 2: Using services for complex business logic
async def authenticate_user_example(email: str, password_hash: str, session: AsyncSession):
    """Example of using service for authentication across multiple user types."""
    user_service = UserService(session)
    return await user_service.authenticate_user(email, password_hash)


async def create_lesson_with_content(
    lesson_data: dict, 
    chunks_data: List[dict], 
    session: AsyncSession
):
    """Example of using service to create lesson with chunks in transaction."""
    lesson_service = LessonService(session)
    return await lesson_service.create_lesson_with_chunks(lesson_data, chunks_data)


async def submit_exam_and_update_ratings(
    student_id: UUID,
    exam_id: UUID, 
    score: float,
    exam_rating: float,
    session: AsyncSession
):
    """Example of using service for complex exam submission logic."""
    exam_service = ExamService(session)
    return await exam_service.submit_exam_result(student_id, exam_id, score, exam_rating)


# Example 3: Using in FastAPI route handlers
"""
# In your FastAPI router file:

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.Api.dependencies import get_db_session, get_user_service, get_lesson_service
from src.Models.services import UserService, LessonService

router = APIRouter()

# Preferred approach: Use service dependencies
@router.get("/students/{student_id}")
async def get_student(
    student_id: UUID, 
    user_service: UserService = Depends(get_user_service)
):
    # Service handles all business logic and transactions
    student = await user_service.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/auth/login")
async def login(
    credentials: LoginSchema,
    user_service: UserService = Depends(get_user_service)
):
    # Service manages authentication across user types
    user_info = await user_service.authenticate_user(
        credentials.email, 
        credentials.password_hash
    )
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user_info

# Alternative: Direct session injection (use only for simple operations)
@router.get("/students/{student_id}/basic")
async def get_student_basic(
    student_id: UUID, 
    session: AsyncSession = Depends(get_db_session)
):
    from src.Models.repositories import StudentRepository
    
    student_repo = StudentRepository(session)
    student = await student_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
"""


# Example 4: Dependency injection pattern
class RepositoryContainer:
    """Container for dependency injection of repositories."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.student_repo = StudentRepository(session)
        self.lesson_repo = LessonRepository(session)
        # Add other repositories as needed


class ServiceContainer:
    """Container for dependency injection of services."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        self.lesson_service = LessonService(session)
        self.exam_service = ExamService(session)


# Example usage with dependency injection
async def complex_business_operation(session: AsyncSession):
    """Example of complex operation using multiple services."""
    services = ServiceContainer(session)
    
    # Authenticate user
    user_info = await services.user_service.authenticate_user("user@example.com", "hash")
    
    if user_info and user_info["user_type"] == "teacher":
        # Get teacher's lessons with statistics
        teacher_stats = await services.lesson_service.get_teacher_lessons_with_stats(
            user_info["user_id"]
        )
        return teacher_stats
    
    return None


# Best Practices Summary:
"""
1. Use repositories for:
   - Simple CRUD operations
   - Model-specific queries
   - Data access layer

2. Use services for:
   - Complex business logic
   - Operations involving multiple models/repositories
   - Transaction management
   - Data validation and processing

3. In FastAPI routes:
   - Inject AsyncSession via Depends()
   - Create repositories/services per request
   - Handle exceptions appropriately
   - Return appropriate HTTP status codes

4. Architecture benefits:
   - Separation of concerns
   - Testability (mock repositories/services)
   - Maintainability
   - Reusability across different API endpoints
"""
