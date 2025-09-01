"""
Main Admin Router
Combines all admin routes into a single router.
"""

from fastapi import APIRouter

from .academic_terms import router as academic_terms_router
from .term_weeks import router as term_weeks_router
from .subjects import router as subjects_router
from .analytics import router as analytics_router
from .id_generation import router as id_generation_router
from .classroom_management import router as classroom_management_router

# Main admin router
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# Include all admin sub-routers
admin_router.include_router(academic_terms_router)
admin_router.include_router(term_weeks_router)
admin_router.include_router(subjects_router)
admin_router.include_router(analytics_router)
admin_router.include_router(id_generation_router)
admin_router.include_router(classroom_management_router)


@admin_router.get("/")
async def admin_dashboard():
    """Admin dashboard endpoint"""
    return {
        "message": "Admin Dashboard",
        "available_endpoints": [
            "/api/v1/admin/academic-terms",
            "/api/v1/admin/term-weeks", 
            "/api/v1/admin/subjects",
            "/api/v1/admin/analytics",
            "/api/v1/admin/id-generation",
            "/api/v1/admin/classrooms"
        ]
    }


@admin_router.get("/health")
async def admin_health_check():
    """Health check for admin routes"""
    return {"status": "healthy", "module": "admin"}
