"""
Term Weeks Admin Routes
Handles CRUD operations for term weeks.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Controllers.admin_controller import AdminController
from src.Api.dependencies import get_db_session, RoleChecker
from src.Api.Schemes.admin import (
    TermWeekCreateModel,
    TermWeekUpdateModel,
    TermWeekResponseModel,
    TermWeekListResponseModel
)

router = APIRouter(prefix="/term-weeks", tags=["Admin - Term Weeks"])

# Role checker for admin access
admin_required = RoleChecker(allowed_roles=["admin"])


@router.post("/", response_model=TermWeekResponseModel)
async def create_term_week(
    week_data: TermWeekCreateModel,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Create a new term week"""
    controller = AdminController(session)
    result = await controller.create_term_week(week_data)
    return result


@router.put("/{week_id}", response_model=TermWeekResponseModel)
async def update_term_week(
    week_id: UUID,
    week_data: TermWeekUpdateModel,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Update a term week"""
    controller = AdminController(session)
    result = await controller.update_term_week(week_id, week_data)
    return result


@router.delete("/{week_id}")
async def delete_term_week(
    week_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Delete a term week"""
    controller = AdminController(session)
    result = await controller.delete_term_week(week_id)
    return {"message": result["message"]}


@router.get("/term/{term_id}", response_model=TermWeekListResponseModel)
async def get_weeks_for_term(
    term_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to retrieve"),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Get all weeks for a specific term"""
    controller = AdminController(session)
    result = await controller.get_weeks_for_term(term_id, skip, limit)
    return result


@router.post("/term/{term_id}/generate")
async def generate_weeks_for_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Auto-generate all weeks for a term based on term duration"""
    controller = AdminController(session)
    result = await controller.generate_weeks_for_term(term_id)
    return result


@router.get("/current")
async def get_current_week(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Get the current active week"""
    controller = AdminController(session)
    result = await controller.week_service.get_current_week()
    return result


@router.get("/term/{term_id}/week/{week_number}")
async def get_week_by_number(
    term_id: UUID,
    week_number: int,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(admin_required)
):
    """Get a specific week by term and week number"""
    controller = AdminController(session)
    result = await controller.week_service.get_week_by_term_and_number(term_id, week_number)
    if not result:
        return {"message": "Week not found"}
    return result
