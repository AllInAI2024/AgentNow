from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20, description="手机号")
    username: str = Field(..., min_length=1, max_length=50, description="用户名")


class UserLogin(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20, description="手机号")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserResponse(BaseModel):
    id: int
    phone: str
    username: str
    role: str
    is_active: bool
    is_default_password: bool
    hermes_profile: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None


class ChangePassword(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=100, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("新密码长度不能少于6位")
        if len(v) > 100:
            raise ValueError("新密码长度不能超过100位")
        return v


class APIResponse(BaseModel):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[dict] = Field(None, description="数据")
