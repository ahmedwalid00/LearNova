from pydantic import BaseModel , Field
from src.Enums.user_type_enums import UserTypeEnum

class UserSignUpModel(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., max_length=15,min_length=6 ,example="securepassword")
    confirm_password: str = Field(..., max_length=15,min_length=6, example="securepassword")
    first_name: str = Field(..., max_length=100,min_length=3 ,example="John")
    last_name: str = Field(..., max_length=100,min_length=3, example="Doe")
    user_unique_id: str = Field(..., example="22001")
    user_type: str = Field(
        ...,
        example=next(iter(UserTypeEnum)).value,
        description=f"One of: {[e.value for e in UserTypeEnum]}"
    )


class UserLoginModel(BaseModel):
    unique_id: str = Field(..., example="22001", description="User's unique identification")
    password: str = Field(..., max_length=15, min_length=6, example="securepassword")


class PasswordResetRequestModel(BaseModel):
    email: str = Field(..., example="user@example.com", description="Email address to send reset link")


class PasswordResetConfirmModel(BaseModel):
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., max_length=15, min_length=6, example="newsecurepassword")
    confirm_password: str = Field(..., max_length=15, min_length=6, example="newsecurepassword")




