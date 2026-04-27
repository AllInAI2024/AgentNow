from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class EnterpriseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="企业名称")
    short_name: Optional[str] = Field(None, max_length=50, description="企业简称")
    code: Optional[str] = Field(None, max_length=50, description="企业代码/统一社会信用代码")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    address: Optional[str] = Field(None, max_length=255, description="企业地址")
    logo_url: Optional[str] = Field(None, max_length=500, description="企业Logo URL")
    description: Optional[str] = Field(None, description="企业描述")
    industry: Optional[str] = Field(None, max_length=100, description="所属行业")
    scale: Optional[str] = Field(None, max_length=50, description="企业规模")


class EnterpriseCreate(EnterpriseBase):
    pass


class EnterpriseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="企业名称")
    short_name: Optional[str] = Field(None, max_length=50, description="企业简称")
    code: Optional[str] = Field(None, max_length=50, description="企业代码/统一社会信用代码")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    address: Optional[str] = Field(None, max_length=255, description="企业地址")
    logo_url: Optional[str] = Field(None, max_length=500, description="企业Logo URL")
    description: Optional[str] = Field(None, description="企业描述")
    industry: Optional[str] = Field(None, max_length=100, description="所属行业")
    scale: Optional[str] = Field(None, max_length=50, description="企业规模")
    is_active: Optional[bool] = Field(None, description="是否激活")


class EnterpriseResponse(EnterpriseBase):
    id: int
    is_active: bool
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
