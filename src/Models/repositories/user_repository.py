"""
User-related repository classes.

This module contains repository classes for user models:
Student, Teacher, Parent, and Admin.
"""

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import and_
from uuid import UUID

from .base import BaseRepository
from ..DBSchemes.Schemes.user_models import Student, Teacher, Parent, Admin
from sqlalchemy.orm import selectinload


class StudentRepository(BaseRepository[Student]):
    """Repository for Student model operations."""
    
    def __init__(self, session):
        super().__init__(session, Student)
    
    async def get_by_email(self, email: str) -> Optional[Student]:
        """Get student by email address."""
        result = await self.session.execute(
            select(Student).where(Student.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_unique_id(self, unique_id: str) -> Optional[Student]:
        """Get student by unique ID."""
        result = await self.session.execute(
            select(Student).where(Student.unique_id == unique_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_parent_id(self, parent_id: UUID) -> List[Student]:
        """Get all students by parent ID."""
        result = await self.session.execute(
            select(Student).where(Student.parent_id == parent_id)
        )
        return result.scalars().all()
    
    async def get_by_term_id(self, term_id: UUID, limit: int = 100, offset: int = 0) -> List[Student]:
        """Get students in a specific term with pagination and eager loading to avoid N+1.

        - limit: max number of records to return (defaults to 100)
        - offset: number of records to skip (defaults to 0)
        """

        # normalize pagination params
        if limit is None or limit <= 0:
            limit = 100
        if offset is None or offset < 0:
            offset = 0

        # build eager-loading options for all relationships on Student to avoid N+1
        options = []
        try:
            options = [selectinload(getattr(Student, rel.key)) for rel in Student.__mapper__.relationships]
        except Exception:
            options = []

        result = await self.session.execute(
            select(Student)
            .where(Student.term_id == term_id)
            .options(*options)
            .limit(limit)
            .offset(offset)
        )
        # use .unique() to guard against duplicates when relationships produce them
        return result.scalars().unique().all()
    
    async def get_by_rating_range(self, min_rating: float, max_rating: float) -> List[Student]:
        """Get students within a specific rating range."""
        result = await self.session.execute(
            select(Student).where(
                and_(
                    Student.rating >= min_rating,
                    Student.rating <= max_rating
                )
            )
        )
        return result.scalars().all()
    
    async def get_verified_students(self) -> List[Student]:
        """Get all verified students."""
        result = await self.session.execute(
            select(Student).where(Student.is_verified == True)
        )
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of student-specific methods."""
        return [
            "get_by_email",
            "get_by_unique_id",
            "get_by_parent_id", 
            "get_by_term_id",
            "get_by_rating_range",
            "get_verified_students"
        ]


class TeacherRepository(BaseRepository[Teacher]):
    """Repository for Teacher model operations."""
    
    def __init__(self, session):
        super().__init__(session, Teacher)
    
    async def get_by_email(self, email: str) -> Optional[Teacher]:
        """Get teacher by email address."""
        result = await self.session.execute(
            select(Teacher).where(Teacher.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_unique_id(self, unique_id: str) -> Optional[Teacher]:
        """Get teacher by unique ID."""
        result = await self.session.execute(
            select(Teacher).where(Teacher.unique_id == unique_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_subject_id(self, subject_id: UUID) -> List[Teacher]:
        """Get all teachers for a specific subject."""
        result = await self.session.execute(
            select(Teacher).where(Teacher.subject_id == subject_id)
        )
        return result.scalars().all()
    
    async def get_by_term_id(self, term_id: UUID) -> List[Teacher]:
        """Get all teachers in a specific term."""
        result = await self.session.execute(
            select(Teacher).where(Teacher.term_id == term_id)
        )
        return result.scalars().all()
    
    async def get_by_rating_range(self, min_rating: float, max_rating: float) -> List[Teacher]:
        """Get teachers within a specific rating range."""
        result = await self.session.execute(
            select(Teacher).where(
                and_(
                    Teacher.rating >= min_rating,
                    Teacher.rating <= max_rating
                )
            )
        )
        return result.scalars().all()
    
    async def get_verified_teachers(self) -> List[Teacher]:
        """Get all verified teachers."""
        result = await self.session.execute(
            select(Teacher).where(Teacher.is_verified == True)
        )
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of teacher-specific methods."""
        return [
            "get_by_email",
            "get_by_unique_id",
            "get_by_subject_id",
            "get_by_term_id", 
            "get_by_rating_range",
            "get_verified_teachers"
        ]


class ParentRepository(BaseRepository[Parent]):
    """Repository for Parent model operations."""
    
    def __init__(self, session):
        super().__init__(session, Parent)
    
    async def get_by_email(self, email: str) -> Optional[Parent]:
        """Get parent by email address."""
        result = await self.session.execute(
            select(Parent).where(Parent.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_unique_id(self, unique_id: str) -> Optional[Parent]:
        """Get parent by unique ID."""
        result = await self.session.execute(
            select(Parent).where(Parent.unique_id == unique_id)
        )
        return result.scalar_one_or_none()
    
    async def get_verified_parents(self) -> List[Parent]:
        """Get all verified parents."""
        result = await self.session.execute(
            select(Parent).where(Parent.is_verified == True)
        )
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of parent-specific methods."""
        return [
            "get_by_email",
            "get_by_unique_id",
            "get_verified_parents"
        ]


class AdminRepository(BaseRepository[Admin]):
    """Repository for Admin model operations."""
    
    def __init__(self, session):
        super().__init__(session, Admin)
    
    async def get_by_email(self, email: str) -> Optional[Admin]:
        """Get admin by email address."""
        result = await self.session.execute(
            select(Admin).where(Admin.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_unique_id(self, unique_id: str) -> Optional[Admin]:
        """Get admin by unique ID."""
        result = await self.session.execute(
            select(Admin).where(Admin.unique_id == unique_id)
        )
        return result.scalar_one_or_none()
    
    def get_model_specific_methods(self):
        """Return list of admin-specific methods."""
        return [
            "get_by_email",
            "get_by_unique_id"
        ]
