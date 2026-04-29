from typing import Optional, List, Generic, TypeVar
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')


class UserBase(BaseModel):
    login_name: str = Field(..., min_length=1, max_length=50, description="登录账号（唯一，用于登录）")
    username: str = Field(..., min_length=1, max_length=50, description="用户姓名/昵称")
    phone: Optional[str] = Field(None, max_length=20, description="手机号（可选，可用于登录）")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")


class UserLogin(BaseModel):
    login_name: str = Field(..., min_length=1, max_length=50, description="登录账号（登录名或手机号）")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    hermes_profile: Optional[str] = Field(None, max_length=100, description="对应的 Hermes Profile 名称")
    hermes_profile_config: Optional[str] = Field(None, description="Hermes Profile 配置(JSON)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户姓名/昵称")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    hermes_profile: Optional[str] = Field(None, max_length=100, description="对应的 Hermes Profile 名称")
    hermes_profile_config: Optional[str] = Field(None, description="Hermes Profile 配置(JSON)")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(BaseModel):
    id: int
    login_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    username: str
    avatar_url: Optional[str] = None
    hermes_profile: Optional[str] = None
    hermes_profile_config: Optional[str] = None
    is_active: bool
    is_default_password: bool
    is_super_admin: bool
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    password_changed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithRolesResponse(UserResponse):
    roles: List[dict] = Field(default_factory=list, description="角色列表")
    permissions: List[dict] = Field(default_factory=list, description="权限列表")


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


class ResetPassword(BaseModel):
    user_id: int = Field(..., description="用户ID")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class AssignRolesRequest(BaseModel):
    role_ids: List[int] = Field(..., description="角色ID列表")


class APIResponse(BaseModel, Generic[T]):
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[T] = Field(None, description="数据")