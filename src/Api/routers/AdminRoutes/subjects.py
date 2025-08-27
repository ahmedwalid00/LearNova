"""
Subjects Admin Routes
Handles CRUD operations for subjects.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Controllers.admin_controller import AdminController
from src.Api.dependencies import get_db_session, RoleChecker
from src.Api.Schemes.admin import (
    SubjectCreateModel,
    SubjectUpdateModel,
    SubjectResponseModel,
    SubjectListResponseModel
)

router = APIRouter(prefix="/subjects", tags=["Admin - Subjects"])

# Role checker for admin access
admin_required = RoleChecker(allowed_roles=["admin"])


@router.post("/", response_model=SubjectResponseModel, dependencies=[Depends(admin_required)])
async def create_subject(
    subject_data: SubjectCreateModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new subject"""
    controller = AdminController(session)
    result = await controller.create_subject(subject_data)
    return result


@router.get("/", dependencies=[Depends(admin_required)])
async def get_all_subjects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get all subjects with pagination"""
    controller = AdminController(session)
    result = await controller.get_all_subjects(skip, limit)
    return result


@router.get("/search", dependencies=[Depends(admin_required)])
async def search_subjects(
    q: str = Query(..., description="Search term for subject name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Search subjects by name"""
    controller = AdminController(session)
    result = await controller.search_subjects(q, skip, limit)
    return result


@router.get("/with-lesson-counts", dependencies=[Depends(admin_required)])
async def get_subjects_with_lesson_counts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get subjects with their lesson counts"""
    controller = AdminController(session)
    result = await controller.get_subjects_with_lesson_counts(skip, limit)
    return result


@router.get("/popular", dependencies=[Depends(admin_required)])
async def get_popular_subjects(
    limit: int = Query(10, ge=1, le=50, description="Number of popular subjects to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get most popular subjects"""
    controller = AdminController(session)
    result = await controller.get_popular_subjects(limit)
    return result


@router.get("/{subject_id}", response_model=SubjectResponseModel, dependencies=[Depends(admin_required)])
async def get_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Get subject by ID"""
    controller = AdminController(session)
    result = await controller.get_subject(subject_id)
    return result


@router.put("/{subject_id}", response_model=SubjectResponseModel, dependencies=[Depends(admin_required)])
async def update_subject(
    subject_id: UUID,
    subject_data: SubjectUpdateModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Update a subject"""
    controller = AdminController(session)
    result = await controller.update_subject(subject_id, subject_data)
    return result


@router.delete("/{subject_id}", dependencies=[Depends(admin_required)])
async def delete_subject(
    subject_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Delete a subject"""
    controller = AdminController(session)
    result = await controller.delete_subject(subject_id)
    return {"message": "Subject deleted successfully"}


@router.get("/name/{subject_name}", dependencies=[Depends(admin_required)])
async def get_subject_by_name(
    subject_name: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get subject by name"""
    controller = AdminController(session)
    result = await controller.subject_service.get_subject_by_name(subject_name)
    if not result:
        return {"message": "Subject not found"}
    return {"subject": result}
