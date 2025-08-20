from pydantic import BaseModel , Field
from src.Enums.user_type_enums import UserTypeEnum

class UserSignUpModel(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., max_length=15,min_length=6 ,example="securepassword")
    confirm_password: str = Field(..., max_length=15,min_length=6, example="securepassword")
    first_name: str = Field(..., max_length=100,min_length=3 ,example="John")
    last_name: str = Field(..., max_length=100,min_length=3, example="Doe")
    user_unique_id: str = Field(..., example="22001")
    user_type : UserTypeEnum = Field(...)


