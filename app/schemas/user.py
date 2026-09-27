from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.base import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    role: UserRole

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include an uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include a lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must include a digit.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
