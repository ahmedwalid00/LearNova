"""
Repository for Term Week operations.
Handles database operations for term weeks.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.orm import selectinload
from datetime import date

from src.Models.DBSchemes.Schemes.term_week import TermWeek
from src.Models.DBSchemes.Schemes.academic_term import AcademicTerm


class TermWeekRepository:
    """Repository for term week operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> TermWeek:
        """Create a new term week"""
        week = TermWeek(**kwargs)
        self.session.add(week)
        await self.session.flush()
        await self.session.refresh(week)
        return week

    async def get_by_id(self, week_id: UUID) -> Optional[TermWeek]:
        """Get term week by ID"""
        result = await self.session.execute(
            select(TermWeek).where(TermWeek.week_id == week_id)
        )
        return result.scalar_one_or_none()

    async def get_by_term_and_week_number(self, term_id: UUID, week_number: int) -> Optional[TermWeek]:
        """Get term week by term ID and week number"""
        result = await self.session.execute(
            select(TermWeek).where(
                and_(
                    TermWeek.term_id == term_id,
                    TermWeek.week_number == week_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_term_id(self, term_id: UUID, skip: int = 0, limit: int = 100) -> List[TermWeek]:
        """Get all weeks for a specific term"""
        result = await self.session.execute(
            select(TermWeek)
            .where(TermWeek.term_id == term_id)
            .order_by(TermWeek.week_number)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_count_by_term_id(self, term_id: UUID) -> int:
        """Get count of weeks for a specific term"""
        result = await self.session.execute(
            select(func.count(TermWeek.week_id))
            .where(TermWeek.term_id == term_id)
        )
        return result.scalar()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[TermWeek]:
        """Get all term weeks with pagination"""
        result = await self.session.execute(
            select(TermWeek)
            .order_by(TermWeek.start_date.desc(), TermWeek.week_number)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_count(self) -> int:
        """Get total count of term weeks"""
        result = await self.session.execute(
            select(func.count(TermWeek.week_id))
        )
        return result.scalar()

    async def get_current_week(self, term_id: UUID = None, current_date: date = None) -> Optional[TermWeek]:
        """Get current week for the given date"""
        if current_date is None:
            current_date = date.today()
        
        query = select(TermWeek).where(
            and_(
                TermWeek.start_date <= current_date,
                TermWeek.end_date >= current_date
            )
        )
        
        if term_id:
            query = query.where(TermWeek.term_id == term_id)
            
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_weeks_with_term(self, skip: int = 0, limit: int = 100) -> List[TermWeek]:
        """Get term weeks with their term information loaded"""
        result = await self.session.execute(
            select(TermWeek)
            .options(selectinload(TermWeek.term))
            .order_by(TermWeek.start_date.desc(), TermWeek.week_number)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, week_id: UUID, **kwargs) -> Optional[TermWeek]:
        """Update term week"""
        result = await self.session.execute(
            update(TermWeek)
            .where(TermWeek.week_id == week_id)
            .values(**kwargs)
            .returning(TermWeek)
        )
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, week_id: UUID) -> bool:
        """Delete term week"""
        result = await self.session.execute(
            delete(TermWeek).where(TermWeek.week_id == week_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def delete_by_term_id(self, term_id: UUID) -> int:
        """Delete all weeks for a specific term"""
        result = await self.session.execute(
            delete(TermWeek).where(TermWeek.term_id == term_id)
        )
        await self.session.flush()
        return result.rowcount

    async def get_overlapping_weeks(self, term_id: UUID, start_date: date, end_date: date, exclude_week_id: UUID = None) -> List[TermWeek]:
        """Get weeks that overlap with the given date range within a term"""
        query = select(TermWeek).where(
            and_(
                TermWeek.term_id == term_id,
                and_(
                    TermWeek.start_date <= end_date,
                    TermWeek.end_date >= start_date
                )
            )
        )
        
        if exclude_week_id:
            query = query.where(TermWeek.week_id != exclude_week_id)
            
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def exists_week_number_in_term(self, term_id: UUID, week_number: int, exclude_week_id: UUID = None) -> bool:
        """Check if a week with the given number exists in the term"""
        query = select(TermWeek.week_id).where(
            and_(
                TermWeek.term_id == term_id,
                TermWeek.week_number == week_number
            )
        )
        
        if exclude_week_id:
            query = query.where(TermWeek.week_id != exclude_week_id)
            
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_weeks_by_date_range(self, start_date: date, end_date: date) -> List[TermWeek]:
        """Get all weeks that fall within the given date range"""
        result = await self.session.execute(
            select(TermWeek)
            .where(
                and_(
                    TermWeek.start_date >= start_date,
                    TermWeek.end_date <= end_date
                )
            )
            .order_by(TermWeek.start_date, TermWeek.week_number)
        )
        return list(result.scalars().all())

    async def get_max_week_number_for_term(self, term_id: UUID) -> int:
        """Get the maximum week number for a term"""
        result = await self.session.execute(
            select(func.max(TermWeek.week_number))
            .where(TermWeek.term_id == term_id)
        )
        max_week = result.scalar()
        return max_week if max_week is not None else 0
