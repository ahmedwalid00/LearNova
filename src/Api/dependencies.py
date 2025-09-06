from datetime import datetime, timedelta, timezone
from fastapi import Depends, Request , status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.Api.utils import JWTHandler 
from src.Helpers.db_session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException
from src.Models.services.authorization_service import AuthorizationService
from src.Models.services.user_service import UserService
from src.Enums.user_type_enums import UserTypeEnum
from src.Models.services.id_generation_service import IDGenerationService
from typing import List, Any

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
        redis_client = request.app.state.redis

        token = creds.credentials

        token_data = JWTHandler.decode_token(token)

        if not self.token_valid(token):
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        self.verify_token_data(token_data)

        if await JWTHandler.is_token_in_blocklist(jti=token_data['jti'] , redis_client=redis_client):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail={
                    "error":"This token is invalid or has been revoked",
                    "resolution":"Please get new token"
                }
            )

        return token_data

    def token_valid(self, token: str) -> bool:
        token_data = JWTHandler.decode_token(token)

        return token_data is not None

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise HTTPException(status_code=401, detail="Expected access token but refresh token provided")


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise HTTPException(status_code=401, detail="Expected refresh token but access token provided")


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_db_session),
):
    # Token payload may contain either a unique_id (preferred) or an email
    token_user = token_details.get("user", {}) if isinstance(token_details, dict) else {}
    unique_id = token_user.get("unique_id") or token_user.get("id")
    email = token_user.get("email")

    # If token carries a unique_id, use AuthorizationService to resolve the user
    if unique_id:
        user = await AuthorizationService.get_user_by_unique_id(session, unique_id)
        if user:
            # Return formatted user dict with proper ID field
            user_id = (
                user.get("student_id") or 
                user.get("teacher_id") or 
                user.get("parent_id") or 
                user.get("admin_id")
            )
            return {
                "id": str(user_id) if user_id else None,
                "unique_id": user.get("unique_id"),
                "email": user.get("email"),
                "name": user.get("name"),
                "is_verified": user.get("is_verified", True),
                "user_type": IDGenerationService.get_user_role_from_id(user.get("unique_id", ""))
            }

    # Fallback: lookup by email across user repositories
    if email:
        service = UserService(session)
        # Try each repository in order: student, teacher, parent, admin
        for repo in (service.student_repo, service.teacher_repo, service.parent_repo, service.admin_repo):
            try:
                candidate = await repo.get_by_email(email)
            except Exception:
                candidate = None
            if candidate:
                # Return formatted user dict with proper ID field
                user_id = (
                    getattr(candidate, "student_id", None) or 
                    getattr(candidate, "teacher_id", None) or 
                    getattr(candidate, "parent_id", None) or
                    getattr(candidate, "admin_id", None)
                )
                return {
                    "id": str(user_id) if user_id else None,
                    "unique_id": getattr(candidate, "unique_id", None),
                    "email": getattr(candidate, "email", None),
                    "name": getattr(candidate, "name", None),
                    "is_verified": getattr(candidate, "is_verified", True),
                    "user_type": IDGenerationService.get_user_role_from_id(getattr(candidate, "unique_id", ""))
                }

    raise HTTPException(status_code=401, detail="Could not resolve user from token")



class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user = Depends(get_current_user)) -> Any:
        # Handle both dictionary and object types for current_user
        if isinstance(current_user, dict):
            unique_id = current_user.get("unique_id")
            is_verified = current_user.get("is_verified", True)  # Default to True for admin
        else:
            unique_id = getattr(current_user, "unique_id", None)
            is_verified = getattr(current_user, "is_verified", True)
        
        if not unique_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
            
        current_user_role = IDGenerationService.get_user_role_from_id(unique_id=unique_id)
        
        if current_user_role in [UserTypeEnum.STUDENT.value, UserTypeEnum.PARENT.value, UserTypeEnum.TEACHER.value]:
            if not is_verified:
                raise HTTPException(status_code=401, detail="Account not verified")

        if current_user_role in self.allowed_roles:
            return True

        raise HTTPException(status_code=403, detail="Insufficient permissions")
