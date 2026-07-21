from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=8, max_length=128)

    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name must not be blank")
        return value


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=1, max_length=128)


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
