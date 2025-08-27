"""
Service for Academic Term business logic.
Handles business rules and validation for academic terms.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.academic_term_repository import AcademicTermRepository
from src.Models.repositories.term_week_repository import TermWeekRepository
from src.Api.Schemes.admin import AcademicTermCreateModel, AcademicTermUpdateModel


class AcademicTermService:
    """Service for academic term business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.term_repo = AcademicTermRepository(session)
        self.week_repo = TermWeekRepository(session)

    async def create_term(self, term_data: AcademicTermCreateModel) -> Dict[str, Any]:
        """Create a new academic term with validation"""
        
        # Check if name already exists
        existing_term = await self.term_repo.get_by_name(term_data.name)
        if existing_term:
            raise ValueError(f"Academic term with name '{term_data.name}' already exists")

        # Check for overlapping date ranges
        overlapping_terms = await self.term_repo.get_overlapping_terms(
            term_data.start_date, term_data.end_date
        )
        if overlapping_terms:
            raise ValueError(
                f"Date range overlaps with existing term(s): {', '.join([t.name for t in overlapping_terms])}"
            )

        # If this term is set as active, deactivate all other terms
        if term_data.is_active:
            await self.term_repo.deactivate_all_terms()

        # Create the term
        term = await self.term_repo.create(**term_data.dict())
        
        return {
            "term": term,
            "message": "Academic term created successfully"
        }

    async def update_term(self, term_id: UUID, term_data: AcademicTermUpdateModel) -> Dict[str, Any]:
        """Update an academic term with validation"""
        
        # Check if term exists
        existing_term = await self.term_repo.get_by_id(term_id)
        if not existing_term:
            raise ValueError("Academic term not found")

        update_data = term_data.dict(exclude_unset=True)
        
        # Check name uniqueness if name is being updated
        if 'name' in update_data:
            name_exists = await self.term_repo.exists_by_name(update_data['name'], term_id)
            if name_exists:
                raise ValueError(f"Academic term with name '{update_data['name']}' already exists")

        # Check for date range overlaps if dates are being updated
        if 'start_date' in update_data or 'end_date' in update_data:
            start_date = update_data.get('start_date', existing_term.start_date)
            end_date = update_data.get('end_date', existing_term.end_date)
            
            overlapping_terms = await self.term_repo.get_overlapping_terms(
                start_date, end_date, term_id
            )
            if overlapping_terms:
                raise ValueError(
                    f"Date range overlaps with existing term(s): {', '.join([t.name for t in overlapping_terms])}"
                )

        # If setting this term as active, deactivate others
        if update_data.get('is_active'):
            await self.term_repo.deactivate_all_terms()

        # Update the term
        updated_term = await self.term_repo.update(term_id, **update_data)
        
        return {
            "term": updated_term,
            "message": "Academic term updated successfully"
        }

    async def delete_term(self, term_id: UUID) -> Dict[str, Any]:
        """Delete an academic term and its related data"""
        
        # Check if term exists
        existing_term = await self.term_repo.get_by_id(term_id)
        if not existing_term:
            raise ValueError("Academic term not found")

        # Delete related weeks first
        deleted_weeks = await self.week_repo.delete_by_term_id(term_id)
        
        # Delete the term
        deleted = await self.term_repo.delete(term_id)
        if not deleted:
            raise ValueError("Failed to delete academic term")
            
        return {
            "message": f"Academic term '{existing_term.name}' deleted successfully",
            "deleted_weeks": deleted_weeks
        }

    async def get_term_by_id(self, term_id: UUID) -> Optional[Dict[str, Any]]:
        """Get academic term by ID with additional info"""
        term = await self.term_repo.get_by_id(term_id)
        if not term:
            return None

        # Get weeks count for this term
        weeks_count = await self.week_repo.get_count_by_term_id(term_id)
        
        return {
            "term": term,
            "weeks_count": weeks_count
        }

    async def get_all_terms(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all academic terms with pagination"""
        terms = await self.term_repo.get_all(skip, limit)
        total = await self.term_repo.get_count()
        
        return {
            "terms": terms,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit
        }

    async def get_active_term(self) -> Optional[Dict[str, Any]]:
        """Get the currently active academic term"""
        term = await self.term_repo.get_active_term()
        if not term:
            return None

        weeks_count = await self.week_repo.get_count_by_term_id(term.term_id)
        
        return {
            "term": term,
            "weeks_count": weeks_count
        }

    async def get_current_term(self, current_date: date = None) -> Optional[Dict[str, Any]]:
        """Get academic term for the current date"""
        term = await self.term_repo.get_current_term(current_date)
        if not term:
            return None

        weeks_count = await self.week_repo.get_count_by_term_id(term.term_id)
        current_week = await self.week_repo.get_current_week(term.term_id, current_date)
        
        return {
            "term": term,
            "weeks_count": weeks_count,
            "current_week": current_week
        }

    async def set_active_term(self, term_id: UUID) -> Dict[str, Any]:
        """Set a term as active and deactivate all others"""
        
        # Check if term exists
        existing_term = await self.term_repo.get_by_id(term_id)
        if not existing_term:
            raise ValueError("Academic term not found")

        # Set as active
        success = await self.term_repo.set_active_term(term_id)
        if not success:
            raise ValueError("Failed to set term as active")
            
        return {
            "term": existing_term,
            "message": f"Academic term '{existing_term.name}' set as active"
        }

    async def get_terms_with_weeks(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get academic terms with their weeks loaded"""
        terms = await self.term_repo.get_terms_with_weeks(skip, limit)
        total = await self.term_repo.get_count()
        
        return {
            "terms": terms,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit
        }

    async def validate_term_dates(self, start_date: date, end_date: date, exclude_term_id: UUID = None) -> bool:
        """Validate that term dates don't overlap with existing terms"""
        overlapping_terms = await self.term_repo.get_overlapping_terms(
            start_date, end_date, exclude_term_id
        )
        return len(overlapping_terms) == 0

    async def get_term_statistics(self, term_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for a term"""
        term = await self.term_repo.get_by_id(term_id)
        if not term:
            raise ValueError("Academic term not found")

        weeks_count = await self.week_repo.get_count_by_term_id(term_id)
        weeks = await self.week_repo.get_by_term_id(term_id)
        
        # Calculate term duration
        duration_days = (term.end_date - term.start_date).days + 1
        
        return {
            "term": term,
            "weeks_count": weeks_count,
            "duration_days": duration_days,
            "weeks": weeks,
            "is_current": term.is_active,
            "status": "active" if term.is_active else "inactive"
        }
