"""
Analytics Admin Routes
Handles analytics report generation and management.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Controllers.admin_controller import AdminController
from src.Api.dependencies import get_db_session, RoleChecker
from src.Api.Schemes.admin import (
    AnalyticsReportCreateModel,
    BulkAnalyticsGenerationModel,
    AnalyticsReportResponseModel
)

router = APIRouter(prefix="/analytics", tags=["Admin - Analytics"])

# Role checker for admin access
admin_required = RoleChecker(allowed_roles=["admin"])


@router.post("/reports", response_model=AnalyticsReportResponseModel, dependencies=[Depends(admin_required)])
async def create_analytics_report(
    report_data: AnalyticsReportCreateModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new analytics report"""
    controller = AdminController(session)
    result = await controller.create_analytics_report(report_data)
    return result["report"]


@router.post("/reports/bulk", dependencies=[Depends(admin_required)])
async def generate_bulk_analytics(
    generation_data: BulkAnalyticsGenerationModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Generate analytics reports in bulk"""
    controller = AdminController(session)
    result = await controller.generate_bulk_analytics(generation_data)
    return result


@router.get("/reports/student/{student_id}", dependencies=[Depends(admin_required)])
async def get_student_analytics_reports(
    student_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get analytics reports for a specific student"""
    controller = AdminController(session)
    result = await controller.get_student_analytics_reports(student_id, skip, limit)
    return {"reports": result}


@router.get("/reports/teacher/{teacher_id}", dependencies=[Depends(admin_required)])
async def get_teacher_analytics_reports(
    teacher_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get analytics reports for a specific teacher"""
    controller = AdminController(session)
    result = await controller.get_teacher_analytics_reports(teacher_id, skip, limit)
    return {"reports": result}


@router.get("/reports/term/{term_id}", dependencies=[Depends(admin_required)])
async def get_term_analytics_reports(
    term_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get analytics reports for a specific term"""
    controller = AdminController(session)
    result = await controller.get_term_analytics_reports(term_id, skip, limit)
    return {"reports": result}


@router.get("/reports/{report_id}", response_model=AnalyticsReportResponseModel, dependencies=[Depends(admin_required)])
async def get_analytics_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Get analytics report by ID"""
    controller = AdminController(session)
    result = await controller.get_analytics_report(report_id)
    if not result:
        return {"message": "Analytics report not found"}
    return result


@router.put("/reports/{report_id}", response_model=AnalyticsReportResponseModel, dependencies=[Depends(admin_required)])
async def update_analytics_report(
    report_id: UUID,
    update_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Update analytics report"""
    controller = AdminController(session)
    result = await controller.update_analytics_report(report_id, update_data)
    return result


@router.delete("/reports/{report_id}", dependencies=[Depends(admin_required)])
async def delete_analytics_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete an analytics report"""
    controller = AdminController(session)
    result = await controller.delete_analytics_report(report_id)
    return {"message": "Analytics report deleted successfully" if result else "Failed to delete report"}
