"""
User service for orchestrating user-related business logic.

This module contains the UserService class that handles complex
operations involving multiple user types and repositories.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.Enums.user_type_enums import UserTypeEnum

from ..repositories.user_repository import (
    StudentRepository, 
    TeacherRepository, 
    ParentRepository, 
    AdminRepository
)


class UserService:
    """
    Service class for user-related business logic.
    
    This class orchestrates operations across different user types
    and provides higher-level business logic methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the service with database session."""
        self.session = session
        self.student_repo = StudentRepository(session)
        self.teacher_repo = TeacherRepository(session)
        self.parent_repo = ParentRepository(session)
        self.admin_repo = AdminRepository(session)
    
    
    async def get_user_by_email_and_type(self, email: str, user_type: UserTypeEnum) -> Optional[Any]:
        """
        Get user by email and specific type.
        
        Args:
            email: User's email address
            user_type: Type of user (student, teacher, parent, admin)
            
        Returns:
            User object or None
        """
        if user_type == UserTypeEnum.STUDENT.value:
            return await self.student_repo.get_by_email(email)
        elif user_type == UserTypeEnum.TEACHER.value:
            return await self.teacher_repo.get_by_email(email)
        elif user_type == UserTypeEnum.PARENT.value:
            return await self.parent_repo.get_by_email(email)
        elif user_type == UserTypeEnum.ADMIN.value:
            return await self.admin_repo.get_by_email(email)
        else:
            return None
    
    async def get_family_info(self, parent_id: UUID) -> Dict[str, Any]:
        """
        Get complete family information including parent and children.
        
        Args:
            parent_id: UUID of the parent
            
        Returns:
            Dict with parent info and list of children
        """
        parent = await self.parent_repo.get_by_id(parent_id)
        children = await self.student_repo.get_by_parent_id(parent_id)
        
        return {
            "parent": parent,
            "children": children,
            "total_children": len(children)
        }
    
    async def get_teacher_classroom_info(self, teacher_id: UUID) -> Dict[str, Any]:
        """
        Get teacher's classroom information including subjects and students.
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dict with teacher and classroom info
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        
        # Note: This would require additional queries to get students
        # through the classroom/association tables
        return {
            "teacher": teacher,
            "subject_id": teacher.subject_id if teacher else None,
            # Additional classroom info would be added here
        }
    
    async def update_user_verification_status(
        self, 
        user_id: UUID, 
        user_type: UserTypeEnum, 
        is_verified: bool
    ) -> bool:
        """
        Update verification status for any user type.
        
        Args:
            user_id: UUID of the user
            user_type: Type of user
            is_verified: New verification status
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if user_type == UserTypeEnum.STUDENT.value:
                result = await self.student_repo.update(user_id, is_verified=is_verified)
            elif user_type == UserTypeEnum.TEACHER.value:
                result = await self.teacher_repo.update(user_id, is_verified=is_verified)
            elif user_type == UserTypeEnum.PARENT.value:
                result = await self.parent_repo.update(user_id, is_verified=is_verified)
            else:
                return False
            
            return result is not None
        except Exception:
            return False
