from datetime import datetime, timedelta, timezone
from fastapi import Depends, Request , status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.Api.utils import JWTHandler 
from src.Helpers.db_session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException
from src.Models.services.authorization_service import AuthorizationService
from src.Models.services.user_service import UserService


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)

        token = creds.credentials

        token_data = JWTHandler.decode_token(token)

        if not self.token_valid(token):
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        self.verify_token_data(token_data)

        if await JWTHandler.is_token_in_blocklist(token_data['jti']):
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
            return user

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
                return candidate

    raise HTTPException(status_code=401, detail="Could not resolve user from token")
