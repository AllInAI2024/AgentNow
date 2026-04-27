from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    parent_id: int = Field(0, description="父部门ID（0表示顶级部门）")
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, max_length=50, description="部门编码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    sort: int = Field(0, description="排序号")
    status: int = Field(1, description="状态：1-启用，0-禁用")
    leader_id: Optional[int] = Field(None, description="部门负责人ID")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    parent_id: Optional[int] = Field(None, description="父部门ID（0表示顶级部门）")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, max_length=50, description="部门编码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    sort: Optional[int] = Field(None, description="排序号")
    status: Optional[int] = Field(None, description="状态：1-启用，0-禁用")
    leader_id: Optional[int] = Field(None, description="部门负责人ID")


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentTreeResponse(DepartmentResponse):
    children: List["DepartmentTreeResponse"] = Field(default_factory=list)


DepartmentTreeResponse.model_rebuild()
