"""
Academic Terms Admin Routes
Handles CRUD operations for academic terms.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Controllers.admin_controller import AdminController
from src.Api.dependencies import get_db_session, RoleChecker
from src.Api.Schemes.admin import (
    AcademicTermCreateModel,
    AcademicTermUpdateModel,
    AcademicTermResponseModel,
    AcademicTermListResponseModel
)

router = APIRouter(prefix="/academic-terms", tags=["Admin - Academic Terms"])

# Role checker for admin access
admin_required = RoleChecker(allowed_roles=["admin"])


@router.post("/", response_model=AcademicTermResponseModel, dependencies=[Depends(admin_required)])
async def create_academic_term(
    term_data: AcademicTermCreateModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new academic term"""
    controller = AdminController(session)
    result = await controller.create_academic_term(term_data)
    return result


@router.get("/", dependencies=[Depends(admin_required)])
async def get_all_academic_terms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Get all academic terms with pagination"""
    controller = AdminController(session)
    result = await controller.get_all_academic_terms(skip, limit)
    return result


@router.get("/{term_id}", response_model=AcademicTermResponseModel, dependencies=[Depends(admin_required)])
async def get_academic_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Get academic term by ID"""
    controller = AdminController(session)
    result = await controller.get_academic_term(term_id)
    return result


@router.put("/{term_id}", response_model=AcademicTermResponseModel)
async def update_academic_term(
    term_id: UUID,
    term_data: AcademicTermUpdateModel,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Update an academic term"""
    controller = AdminController(session)
    result = await controller.update_academic_term(term_id, term_data)
    return result


@router.delete("/{term_id}")
async def delete_academic_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Delete an academic term"""
    controller = AdminController(session)
    result = await controller.delete_academic_term(term_id)
    return {"message": result["message"]}


@router.post("/{term_id}/activate")
async def set_active_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Set a term as the active term"""
    controller = AdminController(session)
    result = await controller.set_active_term(term_id)
    return {"message": result["message"]}


@router.get("/{term_id}/statistics")
async def get_term_statistics(
    term_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Get statistics for a specific term"""
    controller = AdminController(session)
    # This would be implemented in the service layer
    result = await controller.term_service.get_term_statistics(term_id)
    return result
