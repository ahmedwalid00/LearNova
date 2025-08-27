"""
ID Generation Admin Routes
Handles ID generation for students and teachers.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Controllers.admin_controller import AdminController
from src.Api.dependencies import get_db_session, RoleChecker
from src.Api.Schemes.admin import (
    IDGenerationRequestModel,
    IDGenerationResponseModel
)

router = APIRouter(prefix="/id-generation", tags=["Admin - ID Generation"])

# Role checker for admin access
admin_required = RoleChecker(allowed_roles=["admin"])


@router.post("/single", response_model=IDGenerationResponseModel , dependencies=[Depends(admin_required)])
async def generate_single_id(
    request_data: IDGenerationRequestModel,
    session: AsyncSession = Depends(get_db_session)
):
    """Generate a single ID for a user"""
    controller = AdminController(session)
    result = await controller.generate_single_id(request_data)
    return result


@router.post("/bulk" , dependencies=[Depends(admin_required)])
async def generate_bulk_ids(
    user_type: str = Query(..., description="User type (student/teacher)"),
    count: int = Query(..., ge=1, le=1000, description="Number of IDs to generate"),
    session: AsyncSession = Depends(get_db_session)
):      
    """Generate multiple IDs for a user type"""
    controller = AdminController(session)
    result = await controller.generate_bulk_ids(user_type, count)
    return result


@router.get("/check-availability/{unique_id}" , dependencies=[Depends(admin_required)])
async def check_id_availability(
    unique_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Check if an ID is available (not already used)"""
    controller = AdminController(session)
    result = await controller.check_id_availability(unique_id)
    return result


@router.post("/validate" , dependencies=[Depends(admin_required)])
async def validate_id_format(
    unique_id: str = Query(..., description="ID to validate", min_length=5, max_length=5),
    session: AsyncSession = Depends(get_db_session)
):
    """Validate ID format"""
    controller = AdminController(session)
    result = await controller.id_service.validate_id_format(unique_id)
    return result


@router.get("/statistics" , dependencies=[Depends(admin_required)])
async def get_id_statistics(
    session: AsyncSession = Depends(get_db_session)
):
    """Get ID generation statistics for admin dashboard"""
    controller = AdminController(session)
    result = await controller.get_id_statistics()
    return result


@router.post("/reserve" , dependencies=[Depends(admin_required)])
async def reserve_ids(
    user_type: str = Query(..., description="User type (student/teacher)"),
    count: int = Query(..., ge=1, le=1000, description="Number of IDs to reserve"),
    session: AsyncSession = Depends(get_db_session)
):
    """Reserve IDs for future use"""
    controller = AdminController(session)
    # This would call a method to reserve IDs
    result = await controller.id_service.reserve_ids(user_type, count)
    return result
