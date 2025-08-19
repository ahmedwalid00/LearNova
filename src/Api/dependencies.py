"""
FastAPI dependencies for database, authentication, and service injection.
"""

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Optional, Dict, Any

from src.Models.services import UserService, LessonService, ExamService
from src.Models.repositories import (
    StudentRepository, TeacherRepository, ParentRepository, AdminRepository,
    LessonRepository, LessonChunkRepository, ExamRepository, ExamResultRepository,
    AnalyticsRepository
)
from src.Api.utils import JWTHandler


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session for a single request.
    
    This ensures proper transaction management where the entire request
    is treated as a single atomic transaction.
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class TokenBearer(HTTPBearer):
    """
    Custom HTTPBearer for JWT token authentication.
    
    This class handles token extraction, validation, and user authentication
    for protected endpoints.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract and validate JWT token from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Decoded token payload with user information
            
        Raises:
            HTTPException: If token is missing, invalid, or expired
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the access token
        payload = JWTHandler.verify_token(credentials.credentials, JWTHandler.ACCESS_TOKEN)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload


class RefreshTokenBearer(HTTPBearer):
    """
    Custom HTTPBearer specifically for refresh token validation.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract and validate refresh token from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Decoded refresh token payload
            
        Raises:
            HTTPException: If token is missing, invalid, or expired
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the refresh token
        payload = JWTHandler.verify_token(credentials.credentials, JWTHandler.REFRESH_TOKEN)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload


# Security dependency instances
token_bearer = TokenBearer()
refresh_token_bearer = RefreshTokenBearer()


async def get_current_user(
    token_payload: Dict[str, Any] = Depends(token_bearer),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get current authenticated user from token.
    
    Args:
        token_payload: Decoded JWT token payload
        session: Database session
        
    Returns:
        Dictionary containing user information and type
        
    Raises:
        HTTPException: If user not found or invalid
    """
    user_service = UserService(session)
    
    user_id = token_payload.get("sub")
    user_type = token_payload.get("user_type")
    
    if not user_id or not user_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database to ensure they still exist and are active
    user = await user_service.get_user_by_id_and_type(user_id, user_type)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "user": user,
        "user_id": user_id,
        "user_type": user_type,
        "token_payload": token_payload
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user and ensure they are verified/active.
    
    Args:
        current_user: Current user information from token
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If user is not verified or active
    """
    user = current_user["user"]
    
    # Check if user is verified (if your user models have is_verified field)
    if hasattr(user, 'is_verified') and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please check your email."
        )
    
    return current_user


def require_user_type(*allowed_types: str):
    """
    Dependency factory to require specific user types.
    
    Args:
        allowed_types: Allowed user types (student, teacher, parent, admin)
        
    Returns:
        Dependency function that validates user type
    """
    async def check_user_type(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_type = current_user["user_type"]
        
        if user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required user type: {', '.join(allowed_types)}"
            )
        
        return current_user
    
    return check_user_type


# Service Dependencies
def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    """Get UserService instance with injected session."""
    return UserService(session)


def get_lesson_service(session: AsyncSession = Depends(get_db_session)) -> LessonService:
    """Get LessonService instance with injected session."""
    return LessonService(session)


def get_exam_service(session: AsyncSession = Depends(get_db_session)) -> ExamService:
    """Get ExamService instance with injected session."""
    return ExamService(session)


# Repository Dependencies (use these when you need direct repository access)
def get_student_repository(session: AsyncSession = Depends(get_db_session)) -> StudentRepository:
    """Get StudentRepository instance with injected session."""
    return StudentRepository(session)


def get_teacher_repository(session: AsyncSession = Depends(get_db_session)) -> TeacherRepository:
    """Get TeacherRepository instance with injected session."""
    return TeacherRepository(session)


def get_lesson_repository(session: AsyncSession = Depends(get_db_session)) -> LessonRepository:
    """Get LessonRepository instance with injected session."""
    return LessonRepository(session)


def get_exam_repository(session: AsyncSession = Depends(get_db_session)) -> ExamRepository:
    """Get ExamRepository instance with injected session."""
    return ExamRepository(session)


# User type specific dependencies
require_admin = require_user_type("admin")
require_teacher = require_user_type("teacher") 
require_student = require_user_type("student")
require_parent = require_user_type("parent")
require_teacher_or_admin = require_user_type("teacher", "admin")
require_student_or_parent = require_user_type("student", "parent")