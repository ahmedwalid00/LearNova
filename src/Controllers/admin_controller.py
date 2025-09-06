"""
Admin Controller for handling admin-related business logic orchestration.
This controller coordinates between services and routes.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.services.academic_term_service import AcademicTermService
from src.Models.services.term_week_service import TermWeekService
from src.Models.services.subject_service import SubjectService
from src.Models.services.analytics_service import AnalyticsService
from src.Models.services.id_generation_service import IDGenerationService
from src.Api.Schemes.admin import (
    AcademicTermCreateModel, AcademicTermUpdateModel,
    TermWeekCreateModel, TermWeekUpdateModel,
    SubjectCreateModel, SubjectUpdateModel,
    AnalyticsReportCreateModel, BulkAnalyticsGenerationModel,
    IDGenerationRequestModel
)


class AdminController:
    """Controller for admin operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.term_service = AcademicTermService(session)
        self.week_service = TermWeekService(session)
        self.subject_service = SubjectService(session)
        self.analytics_service = AnalyticsService(session)
        self.id_service = IDGenerationService(session)

    # Academic Term Management
    async def create_academic_term(self, term_data: AcademicTermCreateModel) -> Dict[str, Any]:
        """Create a new academic term"""
        try:
            result = await self.term_service.create_term(term_data)
            return result["term"]  # Return just the term object to match AcademicTermResponseModel
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create academic term"
            )

    async def update_academic_term(self, term_id: UUID, term_data: AcademicTermUpdateModel) -> Dict[str, Any]:
        """Update an academic term"""
        try:
            result = await self.term_service.update_term(term_id, term_data)
            return result["term"]  # Return just the term object to match AcademicTermResponseModel
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update academic term"
            )

    async def delete_academic_term(self, term_id: UUID) -> Dict[str, Any]:
        """Delete an academic term"""
        try:
            return await self.term_service.delete_term(term_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete academic term"
            )

    async def get_academic_term(self, term_id: UUID) -> Dict[str, Any]:
        """Get academic term by ID"""
        try:
            result = await self.term_service.get_term_by_id(term_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Academic term not found"
                )
            return result["term"]  # Return just the term object to match AcademicTermResponseModel
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve academic term"
            )

    async def get_all_academic_terms(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all academic terms"""
        try:
            return await self.term_service.get_all_terms(skip, limit)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve academic terms"
            )

    async def set_active_term(self, term_id: UUID) -> Dict[str, Any]:
        """Set a term as active"""
        try:
            return await self.term_service.set_active_term(term_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set active term"
            )

    # Term Week Management
    async def create_term_week(self, week_data: TermWeekCreateModel) -> Dict[str, Any]:
        """Create a new term week"""
        try:
            result = await self.week_service.create_week(week_data)
            return result["week"]  # Return just the week object to match TermWeekResponseModel
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create term week"
            )

    async def update_term_week(self, week_id: UUID, week_data: TermWeekUpdateModel) -> Dict[str, Any]:
        """Update a term week"""
        try:
            result = await self.week_service.update_week(week_id, week_data)
            return result["week"]  # Return just the week object to match TermWeekResponseModel
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update term week"
            )

    async def delete_term_week(self, week_id: UUID) -> Dict[str, Any]:
        """Delete a term week"""
        try:
            return await self.week_service.delete_week(week_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete term week"
            )

    async def generate_weeks_for_term(self, term_id: UUID) -> Dict[str, Any]:
        """Generate all weeks for a term"""
        try:
            return await self.week_service.generate_weeks_for_term(term_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate weeks for term"
            )

    async def get_weeks_for_term(self, term_id: UUID, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all weeks for a term"""
        try:
            return await self.week_service.get_weeks_by_term(term_id, skip, limit)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve term weeks"
            )

    # Subject Management
    async def create_subject(self, subject_data: SubjectCreateModel) -> Dict[str, Any]:
        """Create a new subject"""
        try:
            result = await self.subject_service.create_subject(subject_data)
            return {
                "subject_id": result.subject_id,
                "name": result.name,
                "description": result.description,
                "created_at": result.created_at,
                "updated_at": result.updated_at
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subject"
            )

    async def update_subject(self, subject_id: UUID, subject_data: SubjectUpdateModel) -> Dict[str, Any]:
        """Update a subject"""
        try:
            result = await self.subject_service.update_subject(subject_id, subject_data)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found"
                )
            return {
                "subject_id": result.subject_id,
                "name": result.name,
                "description": result.description,
                "created_at": result.created_at,
                "updated_at": result.updated_at
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subject"
            )

    async def delete_subject(self, subject_id: UUID) -> Dict[str, Any]:
        """Delete a subject"""
        try:
            result = await self.subject_service.delete_subject(subject_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found"
                )
            return {"message": "Subject deleted successfully"}
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete subject"
            )

    async def get_subject(self, subject_id: UUID) -> Dict[str, Any]:
        """Get subject by ID"""
        try:
            result = await self.subject_service.get_subject(subject_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found"
                )
            return {
                "subject_id": result.subject_id,
                "name": result.name,
                "description": result.description,
                "created_at": result.created_at,
                "updated_at": result.updated_at
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subject"
            )

    async def get_all_subjects(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all subjects"""
        try:
            result = await self.subject_service.get_all_subjects(skip, limit)
            return {
                "subjects": result.subjects,
                "total": result.total,
                "page": result.page,
                "size": result.size
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subjects"
            )

    async def search_subjects(self, search_term: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search subjects by name"""
        try:
            result = await self.subject_service.search_subjects(search_term, skip, limit)
            return {
                "subjects": result.subjects,
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "query": search_term
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search subjects"
            )

    async def get_subjects_with_lesson_counts(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get subjects with their lesson counts"""
        try:
            result = await self.subject_service.get_subjects_with_lesson_counts(skip, limit)
            return {
                "subjects": result,
                "total": len(result),
                "page": (skip // limit) + 1,
                "size": limit
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subjects with lesson counts"
            )

    async def get_popular_subjects(self, limit: int = 10) -> Dict[str, Any]:
        """Get popular subjects"""
        try:
            result = await self.subject_service.get_popular_subjects(limit)
            return {
                "subjects": result,
                "message": "Popular subjects retrieved successfully"
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve popular subjects"
            )

    # Analytics Management
    async def create_analytics_report(self, report_data: AnalyticsReportCreateModel) -> Dict[str, Any]:
        """Create an analytics report"""
        try:
            result = await self.analytics_service.create_analytics_report(report_data)
            return {"report": result}
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create analytics report"
            )

    async def get_analytics_report(self, report_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analytics report by ID"""
        try:
            result = await self.analytics_service.get_analytics_report(report_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analytics report not found"
                )
            return {
                "report_id": result.report_id,
                "content": result.content,
                "report_date": result.report_date,
                "student_id": result.student_id,
                "teacher_id": result.teacher_id,
                "week_id": result.week_id,
                "term_id": result.term_id,
                "created_at": result.created_at
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve analytics report"
            )

    async def get_student_analytics_reports(self, student_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get analytics reports for a student"""
        try:
            result = await self.analytics_service.get_student_analytics_reports(student_id, skip, limit)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve student analytics reports"
            )

    async def get_teacher_analytics_reports(self, teacher_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get analytics reports for a teacher"""
        try:
            result = await self.analytics_service.get_teacher_analytics_reports(teacher_id, skip, limit)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve teacher analytics reports"
            )

    async def get_term_analytics_reports(self, term_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get analytics reports for a term"""
        try:
            result = await self.analytics_service.get_term_analytics_reports(term_id, skip, limit)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve term analytics reports"
            )

    async def generate_bulk_analytics(self, generation_data: BulkAnalyticsGenerationModel) -> Dict[str, Any]:
        """Generate analytics reports in bulk"""
        try:
            result = await self.analytics_service.generate_bulk_analytics(generation_data)
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate bulk analytics"
            )

    async def update_analytics_report(self, report_id: UUID, update_data: dict) -> Optional[Dict[str, Any]]:
        """Update analytics report"""
        try:
            result = await self.analytics_service.update_analytics_report(report_id, update_data)
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update analytics report"
            )

    async def delete_analytics_report(self, report_id: UUID) -> bool:
        """Delete analytics report"""
        try:
            result = await self.analytics_service.delete_analytics_report(report_id)
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete analytics report"
            )

    async def get_analytics_summary(self, term_id: UUID = None) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        try:
            # For now, return a basic summary since advanced analytics methods aren't implemented
            return {
                "term_id": str(term_id) if term_id else None,
                "message": "Analytics summary placeholder - to be implemented with advanced analytics"
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve analytics summary"
            )

    # ID Generation Management
    async def generate_single_id(self, request_data: IDGenerationRequestModel, admin_id: UUID) -> Dict[str, Any]:
        """Generate a single ID and create partial user record"""
        try:
            return await self.id_service.generate_single_id(request_data, admin_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate ID"
            )

    async def generate_bulk_ids(self, user_type: str, count: int, admin_id: UUID) -> Dict[str, Any]:
        """Generate multiple IDs and create partial user records"""
        try:
            return await self.id_service.generate_bulk_ids(user_type, count, admin_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate bulk IDs"
            )

    async def check_id_availability(self, unique_id: str) -> Dict[str, Any]:
        """Check if an ID is available"""
        try:
            return await self.id_service.check_id_availability(unique_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check ID availability"
            )

    async def get_id_statistics(self) -> Dict[str, Any]:
        """Get ID generation statistics"""
        try:
            return await self.id_service.get_id_statistics()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve ID statistics"
            )
