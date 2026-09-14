import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.base import CamelModel


class UserOut(CamelModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: Literal["user", "admin"]
    created_at: datetime


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=60)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class AuthResponse(CamelModel):
    access_token: str
    user: UserOut