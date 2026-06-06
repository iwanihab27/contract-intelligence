from enum import Enum


class UserEnums(str, Enum):
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    USER_CREATED_SUCCESSFULLY = "User created successfully"
    INVALID_EMAIL_OR_PASSWORD = "Invalid email or password"
    USER_NOT_FOUND = "User not found"
    ACCOUNT_DELETED = "Account deleted"
    USER_ALREADY_EXISTS = "User already exists"
    INVALID_CREDENTIALS = "Invalid credentials"
    LOGIN_SUCCESS = "Login success"