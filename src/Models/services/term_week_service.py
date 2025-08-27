"""
Service for Term Week business logic.
Handles business rules and validation for term weeks.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.term_week_repository import TermWeekRepository
from src.Models.repositories.academic_term_repository import AcademicTermRepository
from src.Api.Schemes.admin import TermWeekCreateModel, TermWeekUpdateModel


class TermWeekService:
    """Service for term week business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.week_repo = TermWeekRepository(session)
        self.term_repo = AcademicTermRepository(session)

    async def create_week(self, week_data: TermWeekCreateModel) -> Dict[str, Any]:
        """Create a new term week with validation"""
        
        # Check if term exists
        term = await self.term_repo.get_by_id(week_data.term_id)
        if not term:
            raise ValueError("Academic term not found")

        # Validate week dates are within term dates
        if week_data.start_date < term.start_date or week_data.end_date > term.end_date:
            raise ValueError("Week dates must be within the academic term date range")

        # Check if week number already exists for this term
        existing_week = await self.week_repo.get_by_term_and_week_number(
            week_data.term_id, week_data.week_number
        )
        if existing_week:
            raise ValueError(f"Week {week_data.week_number} already exists for this term")

        # Check for overlapping date ranges within the term
        overlapping_weeks = await self.week_repo.get_overlapping_weeks(
            week_data.term_id, week_data.start_date, week_data.end_date
        )
        if overlapping_weeks:
            raise ValueError(
                f"Date range overlaps with existing week(s): {', '.join([str(w.week_number) for w in overlapping_weeks])}"
            )

        # Create the week
        week = await self.week_repo.create(**week_data.dict())
        
        return {
            "week": week,
            "message": "Term week created successfully"
        }

    async def update_week(self, week_id: UUID, week_data: TermWeekUpdateModel) -> Dict[str, Any]:
        """Update a term week with validation"""
        
        # Check if week exists
        existing_week = await self.week_repo.get_by_id(week_id)
        if not existing_week:
            raise ValueError("Term week not found")

        # Get the term for validation
        term = await self.term_repo.get_by_id(existing_week.term_id)
        if not term:
            raise ValueError("Associated academic term not found")

        update_data = week_data.dict(exclude_unset=True)
        
        # Check week number uniqueness if being updated
        if 'week_number' in update_data:
            week_exists = await self.week_repo.exists_week_number_in_term(
                existing_week.term_id, update_data['week_number'], week_id
            )
            if week_exists:
                raise ValueError(f"Week {update_data['week_number']} already exists for this term")

        # Validate dates are within term if being updated
        if 'start_date' in update_data or 'end_date' in update_data:
            start_date = update_data.get('start_date', existing_week.start_date)
            end_date = update_data.get('end_date', existing_week.end_date)
            
            if start_date < term.start_date or end_date > term.end_date:
                raise ValueError("Week dates must be within the academic term date range")

            # Check for overlapping date ranges
            overlapping_weeks = await self.week_repo.get_overlapping_weeks(
                existing_week.term_id, start_date, end_date, week_id
            )
            if overlapping_weeks:
                raise ValueError(
                    f"Date range overlaps with existing week(s): {', '.join([str(w.week_number) for w in overlapping_weeks])}"
                )

        # Update the week
        updated_week = await self.week_repo.update(week_id, **update_data)
        
        return {
            "week": updated_week,
            "message": "Term week updated successfully"
        }

    async def delete_week(self, week_id: UUID) -> Dict[str, Any]:
        """Delete a term week"""
        
        # Check if week exists
        existing_week = await self.week_repo.get_by_id(week_id)
        if not existing_week:
            raise ValueError("Term week not found")

        # Delete the week
        deleted = await self.week_repo.delete(week_id)
        if not deleted:
            raise ValueError("Failed to delete term week")
            
        return {
            "message": f"Term week {existing_week.week_number} deleted successfully"
        }

    async def get_week_by_id(self, week_id: UUID) -> Optional[Dict[str, Any]]:
        """Get term week by ID"""
        week = await self.week_repo.get_by_id(week_id)
        if not week:
            return None

        # Get term information
        term = await self.term_repo.get_by_id(week.term_id)
        
        return {
            "week": week,
            "term": term
        }

    async def get_weeks_by_term(self, term_id: UUID, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all weeks for a specific term"""
        
        # Check if term exists
        term = await self.term_repo.get_by_id(term_id)
        if not term:
            raise ValueError("Academic term not found")

        weeks = await self.week_repo.get_by_term_id(term_id, skip, limit)
        total = await self.week_repo.get_count_by_term_id(term_id)
        
        return {
            "weeks": weeks,
            "term": term,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit
        }

    async def get_all_weeks(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all term weeks with pagination"""
        weeks = await self.week_repo.get_all(skip, limit)
        total = await self.week_repo.get_count()
        
        return {
            "weeks": weeks,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit
        }

    async def get_current_week(self, term_id: UUID = None, current_date: date = None) -> Optional[Dict[str, Any]]:
        """Get current week for the given date"""
        week = await self.week_repo.get_current_week(term_id, current_date)
        if not week:
            return None

        term = await self.term_repo.get_by_id(week.term_id)
        
        return {
            "week": week,
            "term": term
        }

    async def generate_weeks_for_term(self, term_id: UUID, weeks_count: int = None) -> Dict[str, Any]:
        """Auto-generate weeks for a term"""
        
        # Check if term exists
        term = await self.term_repo.get_by_id(term_id)
        if not term:
            raise ValueError("Academic term not found")

        # Check if term already has weeks
        existing_weeks = await self.week_repo.get_by_term_id(term_id)
        if existing_weeks:
            raise ValueError("Term already has weeks configured")

        # Calculate number of weeks if not provided
        if weeks_count is None:
            term_duration = (term.end_date - term.start_date).days
            weeks_count = min(term_duration // 7, 20)  # Max 20 weeks

        if weeks_count <= 0:
            raise ValueError("Invalid number of weeks")

        # Generate weeks
        weeks_created = []
        current_start = term.start_date
        
        for week_num in range(1, weeks_count + 1):
            week_end = current_start + timedelta(days=6)
            
            # Don't exceed term end date
            if week_end > term.end_date:
                week_end = term.end_date

            week_data = {
                "term_id": term_id,
                "week_number": week_num,
                "start_date": current_start,
                "end_date": week_end
            }
            
            week = await self.week_repo.create(**week_data)
            weeks_created.append(week)
            
            # Move to next week
            current_start = week_end + timedelta(days=1)
            
            # Stop if we've reached the term end
            if current_start > term.end_date:
                break

        return {
            "weeks": weeks_created,
            "term": term,
            "message": f"Generated {len(weeks_created)} weeks for term '{term.name}'"
        }

    async def get_week_statistics(self, week_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for a week"""
        week = await self.week_repo.get_by_id(week_id)
        if not week:
            raise ValueError("Term week not found")

        term = await self.term_repo.get_by_id(week.term_id)
        
        # Calculate week duration
        duration_days = (week.end_date - week.start_date).days + 1
        
        return {
            "week": week,
            "term": term,
            "duration_days": duration_days,
            "is_current": self._is_current_week(week),
            "status": self._get_week_status(week)
        }

    def _is_current_week(self, week) -> bool:
        """Check if the week is the current week"""
        today = date.today()
        return week.start_date <= today <= week.end_date

    def _get_week_status(self, week) -> str:
        """Get the status of the week (past, current, future)"""
        today = date.today()
        if today < week.start_date:
            return "future"
        elif today > week.end_date:
            return "past"
        else:
            return "current"

    async def get_week_by_term_and_number(self, term_id: UUID, week_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific week by term ID and week number"""
        week = await self.week_repo.get_by_term_and_week_number(term_id, week_number)
        if not week:
            return None
        
        return {
            "week": week,
            "week_number": week.week_number,
            "term_id": week.term_id,
            "start_date": week.start_date,
            "end_date": week.end_date
        }
