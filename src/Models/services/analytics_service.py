"""
Service for Analytics business logic.
Handles analytics report generation and analysis.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.analytics_repository import AnalyticsRepository
from src.Models.repositories.academic_term_repository import AcademicTermRepository
from src.Models.repositories.term_week_repository import TermWeekRepository
from src.Api.Schemes.admin import (
    AnalyticsReportCreateModel, 
    AnalyticsReportResponseModel,
    BulkAnalyticsGenerationModel
)


class AnalyticsService:
    """Service for analytics business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics_repo = AnalyticsRepository(session)
        self.term_repo = AcademicTermRepository(session)
        self.week_repo = TermWeekRepository(session)

    async def create_analytics_report(self, report_data: AnalyticsReportCreateModel) -> AnalyticsReportResponseModel:
        """Create a new analytics report"""
        
        # Validate term exists
        term = await self.term_repo.get_by_id(report_data.term_id)
        if not term:
            raise ValueError("Academic term not found")

        # Validate week exists if provided
        if report_data.week_id:
            week = await self.week_repo.get_by_id(report_data.week_id)
            if not week:
                raise ValueError("Term week not found")

        # Generate report content
        content = await self._generate_report_content(report_data)
        
        # Create report data
        report_dict = {
            "content": content,
            "report_date": date.today(),
            "student_id": report_data.student_id,
            "teacher_id": report_data.teacher_id,
            "week_id": report_data.week_id,
            "term_id": report_data.term_id
        }
        
        analytics_report = await self.analytics_repo.create(**report_dict)
        await self.session.flush()
        
        return AnalyticsReportResponseModel(
            report_id=analytics_report.report_id,
            content=analytics_report.content,
            report_date=analytics_report.report_date,
            student_id=analytics_report.student_id,
            teacher_id=analytics_report.teacher_id,
            week_id=analytics_report.week_id,
            term_id=analytics_report.term_id,
            created_at=analytics_report.created_at
        )

    async def get_analytics_report(self, report_id: UUID) -> Optional[AnalyticsReportResponseModel]:
        """Get analytics report by ID"""
        analytics_report = await self.analytics_repo.get_by_id(report_id)
        if not analytics_report:
            return None
            
        return AnalyticsReportResponseModel(
            report_id=analytics_report.report_id,
            content=analytics_report.content,
            report_date=analytics_report.report_date,
            student_id=analytics_report.student_id,
            teacher_id=analytics_report.teacher_id,
            week_id=analytics_report.week_id,
            term_id=analytics_report.term_id,
            created_at=analytics_report.created_at
        )

    async def get_student_analytics_reports(self, student_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyticsReportResponseModel]:
        """Get all analytics reports for a student"""
        reports = await self.analytics_repo.get_by_student_id(student_id)
        
        # Apply pagination manually
        paginated_reports = reports[skip:skip + limit] if reports else []
        
        return [
            AnalyticsReportResponseModel(
                report_id=report.report_id,
                content=report.content,
                report_date=report.report_date,
                student_id=report.student_id,
                teacher_id=report.teacher_id,
                week_id=report.week_id,
                term_id=report.term_id,
                created_at=report.created_at
            )
            for report in paginated_reports
        ]

    async def get_teacher_analytics_reports(self, teacher_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyticsReportResponseModel]:
        """Get all analytics reports for a teacher"""
        reports = await self.analytics_repo.get_by_teacher_id(teacher_id)
        
        # Apply pagination manually
        paginated_reports = reports[skip:skip + limit] if reports else []
        
        return [
            AnalyticsReportResponseModel(
                report_id=report.report_id,
                content=report.content,
                report_date=report.report_date,
                student_id=report.student_id,
                teacher_id=report.teacher_id,
                week_id=report.week_id,
                term_id=report.term_id,
                created_at=report.created_at
            )
            for report in paginated_reports
        ]

    async def get_term_analytics_reports(self, term_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyticsReportResponseModel]:
        """Get all analytics reports for a term"""
        reports = await self.analytics_repo.get_by_term_id(term_id)
        
        # Apply pagination manually
        paginated_reports = reports[skip:skip + limit] if reports else []
        
        return [
            AnalyticsReportResponseModel(
                report_id=report.report_id,
                content=report.content,
                report_date=report.report_date,
                student_id=report.student_id,
                teacher_id=report.teacher_id,
                week_id=report.week_id,
                term_id=report.term_id,
                created_at=report.created_at
            )
            for report in paginated_reports
        ]

    async def generate_bulk_analytics(self, bulk_data: BulkAnalyticsGenerationModel) -> Dict[str, Any]:
        """Generate analytics reports in bulk"""
        try:
            # Validate term exists
            term = await self.term_repo.get_by_id(bulk_data.term_id)
            if not term:
                raise ValueError("Academic term not found")

            # Validate week exists if provided
            if bulk_data.week_id:
                week = await self.week_repo.get_by_id(bulk_data.week_id)
                if not week:
                    raise ValueError("Term week not found")

            generated_count = 0
            
            # For now, return a placeholder response since we don't have student/teacher repositories integrated
            # This would be implemented when student and teacher services are available
            
            return {
                "generated_count": generated_count,
                "report_type": bulk_data.report_type,
                "term_id": str(bulk_data.term_id),
                "week_id": str(bulk_data.week_id) if bulk_data.week_id else None,
                "target_users": bulk_data.target_users,
                "message": "Bulk analytics generation completed"
            }
        except Exception as e:
            await self.session.rollback()
            raise e

    async def update_analytics_report(self, report_id: UUID, update_data: dict) -> Optional[AnalyticsReportResponseModel]:
        """Update an analytics report"""
        try:
            analytics_report = await self.analytics_repo.update(report_id, **update_data)
            if not analytics_report:
                return None
                
            await self.session.flush()
            
            return AnalyticsReportResponseModel(
                report_id=analytics_report.report_id,
                content=analytics_report.content,
                report_date=analytics_report.report_date,
                student_id=analytics_report.student_id,
                teacher_id=analytics_report.teacher_id,
                week_id=analytics_report.week_id,
                term_id=analytics_report.term_id,
                created_at=analytics_report.created_at
            )
        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete_analytics_report(self, report_id: UUID) -> bool:
        """Delete an analytics report"""
        try:
            success = await self.analytics_repo.delete(report_id)
            if success:
                await self.session.flush()
            return success
        except Exception as e:
            await self.session.rollback()
            raise e

    async def _generate_report_content(self, report_data: AnalyticsReportCreateModel) -> str:
        """Generate report content based on report data"""
        # TODO: Implement actual report generation logic
        # This could include analysis of student performance, attendance, etc.
        
        if report_data.student_id:
            return f"Individual student report for student {report_data.student_id} - {report_data.report_type}"
        elif report_data.teacher_id:
            return f"Teacher report for teacher {report_data.teacher_id} - {report_data.report_type}"
        else:
            return f"General {report_data.report_type} report for term {report_data.term_id}"
