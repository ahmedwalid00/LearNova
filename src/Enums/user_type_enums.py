from enum import Enum

class UserTypeEnum(Enum):
    """User type enumeration for the platform"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"

class UserIDPrefix(Enum):
    """Unique ID prefixes for different user roles"""
    STUDENT = "22"
    TEACHER = "11"
    ADMIN = "ADMIN"
    PARENT = "P"


