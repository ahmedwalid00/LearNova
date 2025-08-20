from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.Api.Schemes import user
from src.Helpers.db_session import get_db_session
from ..Schemes.auth_schemes import UserSignUpModel 
from src.Models.repositories.user_repository import StudentRepository, TeacherRepository , ParentRepository
from src.Enums.signal_response import SignalResponse
from src.Enums.user_type_enums import UserTypeEnum
from src.Models.services.id_generation_service import IDGenerationService
from ..utils import PasswordHandler

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger('uvicorn.error')

auth_router = APIRouter(prefix="/api/v1/auth",
                        tags=["Authentication"])


@auth_router.post("/sign-up")
async def sign_up(user_data: UserSignUpModel, session: AsyncSession = Depends(get_db_session)):
    email = user_data.email.lower()
    first_name = user_data.first_name
    last_name = user_data.last_name
    user_unique_id = user_data.user_unique_id
    user_type = user_data.user_type
    password = user_data.password
    confirm_password = user_data.confirm_password

    expected_user = IDGenerationService.get_user_role_from_id(unique_id=user_unique_id)
    if expected_user != user_type:
        logger.error(f"User type mismatch: expected {expected_user}, got {user_type}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SignalResponse.ID_DOESNT_MATCH_ROLE.value)
    
    if user_type == UserTypeEnum.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin accounts cannot self-register")
    
    if user_type == UserTypeEnum.STUDENT.value:
        user_repo = StudentRepository(session)
    elif user_type == UserTypeEnum.TEACHER.value:
        user_repo = TeacherRepository(session)
    elif user_type == UserTypeEnum.PARENT.value:
        user_repo = ParentRepository(session)

    check_email = await user_repo.get_user_by_email(email=email)
    if check_email:
        logger.error(f"Email already registered: {email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SignalResponse.EMAIL_ALREADY_REGISTERED.value)

    check_unique_id = await user_repo.get_user_by_unique_id(unique_id=user_unique_id)
    if check_unique_id:
        logger.error(f"Unique ID already registered: {user_unique_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SignalResponse.UNIQUE_ID_ALREADY_REGISTERED.value)

    if password != confirm_password:
        logger.error("Passwords do not match")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SignalResponse.PASSWORD_NOT_MATCH.value)

    combined_name = f"{first_name} {last_name}"

    hashed_password = PasswordHandler.hash_password(password)

    new_user = user_repo.create_user(email=email,
                                    name=combined_name,
                                    password_hash=hashed_password,
                                    unique_id=user_unique_id)
    
    #TODO : email verification logic
    # Celery to Handle the email verification

    user_out = {
        "id": getattr(new_user, "id", None),
        "unique_id": getattr(new_user, "unique_id", None),
        "email": getattr(new_user, "email", None),
        "name": getattr(new_user, "name", None),
    }

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": SignalResponse.SIGNUP_SUCCESS.value,
                                                                      "user": user_out})
