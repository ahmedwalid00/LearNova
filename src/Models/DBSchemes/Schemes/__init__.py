# Import all database models for proper relationship resolution
from .base import BaseModel
from .user_models import Student, Teacher, Parent, Admin
from .associations import ParentStudentLink

__all__ = [
    "BaseModel",
    "Student", 
    "Teacher", 
    "Parent", 
    "Admin",
    "ParentStudentLink",
]
