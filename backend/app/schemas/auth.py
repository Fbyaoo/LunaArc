
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):

    email: EmailStr

    password: str

    display_name: str



class LoginRequest(BaseModel):

    email: EmailStr

    password: str



class UserResponse(BaseModel):

    id: int

    email: str

    display_name: str

    plan: str



class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserResponse


class RefreshResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

