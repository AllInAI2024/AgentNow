from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限编码（英文标识）")
    type: int = Field(1, description="类型：1-菜单，2-按钮，3-API接口")
    parent_id: int = Field(0, description="父权限ID（0表示顶级）")
    path: Optional[str] = Field(None, max_length=255, description="路由路径/接口路径")
    icon: Optional[str] = Field(None, max_length=100, description="菜单图标")


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="权限名称")
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="权限编码（英文标识）")
    type: Optional[int] = Field(None, description="类型：1-菜单，2-按钮，3-API接口")
    parent_id: Optional[int] = Field(None, description="父权限ID（0表示顶级）")
    path: Optional[str] = Field(None, max_length=255, description="路由路径/接口路径")
    icon: Optional[str] = Field(None, max_length=100, description="菜单图标")


class PermissionResponse(PermissionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PermissionTreeResponse(PermissionResponse):
    children: List["PermissionTreeResponse"] = Field(default_factory=list)


PermissionTreeResponse.model_rebuild()