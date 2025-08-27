"""
Repository for Academic Term operations.
Handles database operations for academic terms.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
from datetime import date

from .base import BaseRepository
from ..DBSchemes.Schemes.academic_term import AcademicTerm
from ..DBSchemes.Schemes.term_week import TermWeek


class AcademicTermRepository(BaseRepository[AcademicTerm]):
    """Repository for academic term operations"""

    def __init__(self, session):
        super().__init__(session, AcademicTerm)

    async def get_by_name(self, name: str) -> Optional[AcademicTerm]:
        """Get academic term by name"""
        result = await self.session.execute(
            select(AcademicTerm).where(AcademicTerm.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active_term(self) -> Optional[AcademicTerm]:
        """Get the currently active academic term"""
        result = await self.session.execute(
            select(AcademicTerm).where(AcademicTerm.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_overlapping_terms(self, start_date: date, end_date: date, exclude_term_id: UUID = None) -> List[AcademicTerm]:
        """Get terms that overlap with the given date range"""
        query = select(AcademicTerm).where(
            or_(
                and_(AcademicTerm.start_date <= end_date, AcademicTerm.end_date >= start_date)
            )
        )
        
        if exclude_term_id:
            query = query.where(AcademicTerm.term_id != exclude_term_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def exists_by_name(self, name: str, exclude_term_id: UUID = None) -> bool:
        """Check if a term with the given name exists"""
        query = select(AcademicTerm.term_id).where(AcademicTerm.name == name)
        
        if exclude_term_id:
            query = query.where(AcademicTerm.term_id != exclude_term_id)
            
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def set_active_term(self, term_id: UUID) -> bool:
        """Set a term as active and deactivate all others"""
        # First deactivate all terms
        await self.deactivate_all_terms()
        
        # Then activate the specified term
        result = await self.update(term_id, is_active=True)
        return result is not None

    async def deactivate_all_terms(self) -> int:
        """Deactivate all terms"""
        result = await self.session.execute(
            update(AcademicTerm).values(is_active=False)
        )
        await self.session.flush()
        return result.rowcount

    async def get_terms_with_weeks_count(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get terms with their week count"""
        result = await self.session.execute(
            select(
                AcademicTerm.term_id,
                AcademicTerm.name,
                AcademicTerm.start_date,
                AcademicTerm.end_date,
                AcademicTerm.is_active,
                AcademicTerm.created_at,
                AcademicTerm.updated_at,
                func.count(TermWeek.week_id).label('weeks_count')
            )
            .outerjoin(TermWeek, AcademicTerm.term_id == TermWeek.term_id)
            .group_by(
                AcademicTerm.term_id,
                AcademicTerm.name,
                AcademicTerm.start_date,
                AcademicTerm.end_date,
                AcademicTerm.is_active,
                AcademicTerm.created_at,
                AcademicTerm.updated_at
            )
            .order_by(AcademicTerm.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        
        return [
            {
                "term_id": row.term_id,
                "name": row.name,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "is_active": row.is_active,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "weeks_count": row.weeks_count or 0
            }
            for row in result
        ]

    async def get_terms_by_date_range(self, start_date: date, end_date: date) -> List[AcademicTerm]:
        """Get terms within a specific date range"""
        result = await self.session.execute(
            select(AcademicTerm).where(
                and_(
                    AcademicTerm.start_date >= start_date,
                    AcademicTerm.end_date <= end_date
                )
            ).order_by(AcademicTerm.start_date)
        )
        return list(result.scalars().all())

    async def get_count(self) -> int:
        """Get total count of academic terms"""
        return await self.count()

    async def get_current_term(self, current_date: date = None) -> Optional[AcademicTerm]:
        """Get academic term for the current date"""
        if current_date is None:
            current_date = date.today()
            
        result = await self.session.execute(
            select(AcademicTerm).where(
                and_(
                    AcademicTerm.start_date <= current_date,
                    AcademicTerm.end_date >= current_date
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_terms_with_weeks(self, skip: int = 0, limit: int = 100) -> List[AcademicTerm]:
        """Get academic terms with their weeks loaded"""
        result = await self.session.execute(
            select(AcademicTerm)
            .options(selectinload(AcademicTerm.term_weeks))
            .order_by(AcademicTerm.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    def get_model_specific_methods(self):
        """Return list of academic term-specific methods."""
        return [
            "get_by_name",
            "get_active_term",
            "get_overlapping_terms",
            "exists_by_name",
            "set_active_term",
            "deactivate_all_terms",
            "get_terms_with_weeks_count",
            "get_terms_by_date_range"
        ]
