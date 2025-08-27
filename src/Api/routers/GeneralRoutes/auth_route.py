from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.Api.utils import JWTHandler
from src.Helpers.db_session import get_db_session
from src.Helpers.redis import get_redis_client
from src.Api.Schemes.auth_schemes import UserSignUpModel, UserLoginModel, PasswordResetRequestModel, PasswordResetConfirmModel
from src.Controllers.auth_controller import AuthController
from ...dependencies import AccessTokenBearer , RefreshTokenBearer   
from src.email import create_message, mail

from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import logging
import aioredis

logger = logging.getLogger('uvicorn.error')

auth_router = APIRouter(prefix="/api/v1/auth",
                        tags=["Authentication"])


@auth_router.post("/sign-up")
async def sign_up(user_data: UserSignUpModel, session: AsyncSession = Depends(get_db_session)):
    """
    Register a new user account.
    
    This endpoint handles user registration for students, teachers, and parents.
    Admin accounts cannot self-register and must be created through admin processes.
    """
    auth_controller = AuthController(session)
    result = await auth_controller.signup_user(user_data)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content=result
    )


@auth_router.post("/login")
async def login(login_data: UserLoginModel, session: AsyncSession = Depends(get_db_session)):
    """
    Authenticate a user and return access tokens.
    
    This endpoint authenticates users using their unique_id and password,
    then returns JWT tokens for accessing protected resources.
    """
    auth_controller = AuthController(session)
    result = await auth_controller.login_user(login_data.unique_id, login_data.password)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )



@auth_router.get("/verify-email")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Verify user email using verification token.
    
    This endpoint is called when users click the verification link in their email.
    It validates the token and marks the user's email as verified.
    """
    auth_controller = AuthController(session)
    result = await auth_controller.verify_email(token)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )


@auth_router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequestModel,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Request password reset for a user.
    
    This endpoint sends a password reset email to the user with a secure reset link.
    The user can then use this link to set a new password.
    """
    auth_controller = AuthController(session)
    result = await auth_controller.request_password_reset(reset_data.email)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )


@auth_router.post("/confirm-password-reset")
async def confirm_password_reset(
    reset_data: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Confirm password reset using reset token.
    
    This endpoint is used to complete the password reset process.
    It validates the reset token and updates the user's password.
    """
    auth_controller = AuthController(session)
    result = await auth_controller.confirm_password_reset(
        token=reset_data.token,
        new_password=reset_data.new_password,
        confirm_password=reset_data.confirm_password
    )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )


@auth_router.get('/logout')
async def revoke_token(token_details:dict=Depends(AccessTokenBearer()) , redis_client: aioredis.Redis = Depends(get_redis_client)):
    try:
        jti = token_details['jti']

        _ = await JWTHandler.add_jti_to_blocklist(jti=jti, redis_client=redis_client)

        return JSONResponse(
            content={
                "message":"Logged Out Successfully"
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"}
        )
    
@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = JWTHandler.create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})
    else:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Token has expired"}
        )


@auth_router.post("/send_mail")
async def send_mail():
    emails = ["ahmed.walid5@msa.edu.eg"]

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    message = create_message(recipients=emails, subject=subject, body=html)
    await mail.send_message(message)

    return {"message": "Email sent successfully"}





