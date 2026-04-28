from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KnowledgeDocBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, max_length=100, description="文档分类")
    is_public: bool = Field(True, description="是否公开")


class KnowledgeDocCreate(KnowledgeDocBase):
    pass


class KnowledgeDocUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


class KnowledgeDocContentUpdate(BaseModel):
    content: str = Field(..., description="文档内容（Markdown 或文本）")


class KnowledgeDocResponse(KnowledgeDocBase):
    id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    created_by: int
    updated_by: Optional[int] = None
    word_count: Optional[int] = None
    file_modified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeDocDetailResponse(KnowledgeDocResponse):
    content: Optional[str] = None


class KnowledgeDocListResponse(BaseModel):
    items: List[KnowledgeDocResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeConfigBase(BaseModel):
    config_key: str = Field(..., max_length=100, description="配置键")
    config_value: str = Field(..., description="配置值")


class KnowledgeConfigUpdate(BaseModel):
    config_value: str = Field(..., description="配置值")


class KnowledgeConfigResponse(KnowledgeConfigBase):
    id: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeleteResult(BaseModel):
    success: bool
    message: str


class UploadResult(BaseModel):
    doc: KnowledgeDocResponse
    message: str = "上传成功"


class ContentUpdateResult(BaseModel):
    doc: KnowledgeDocResponse
    content: str
    message: str = "内容更新成功"


class AllTagsResponse(BaseModel):
    tags: List[str]
    total: int


class AllCategoriesResponse(BaseModel):
    categories: List[str]
    total: int


class FileSystemInfo(BaseModel):
    base_path: str
    total_files: int
    total_size: int
    free_space: int


class StatisticsResponse(BaseModel):
    total_docs: int
    total_size: int
    total_categories: int
    total_tags: int
    public_docs: int
    recent_uploads: int
