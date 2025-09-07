"""
Student Routes Module

This module exports all student-related API routes.
"""

from fastapi import APIRouter
from .student_response_router import router as student_response_router

# Create main student router
router = APIRouter()

# Include all student sub-routers
router.include_router(student_response_router)

__all__ = ["router"]
