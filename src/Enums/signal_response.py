from enum import Enum

class SignalResponse(Enum):
    SIGNUP_SUCCESS = "Account Created! Check email to verify your account"
    SIGNUP_FAILURE = "signup_failure"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_NOT_MATCH = "Passwords do not match"
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    ID_DOESNT_MATCH_ROLE = "User ID does not match role"
    UNIQUE_ID_ALREADY_REGISTERED = "ID already registered"
    INVALID_USER_TYPE = "Invalid user type"
    USER_NOT_FOUND = "User not found"
    NO_FILE_UPLOADED = "No file uploaded"
    NO_FILE_NAME_PROVIDED = "No file name provided"


    