from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码（英文标识）")
    description: Optional[str] = Field(None, description="角色描述")


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")


class RoleResponse(RoleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleWithPermissionsResponse(RoleResponse):
    permissions: List[int] = Field(default_factory=list, description="权限ID列表")


class AssignPermissionsRequest(BaseModel):
    permission_ids: List[int] = Field(..., description="权限ID列表")