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


class KnowledgeDocResponse(KnowledgeDocBase):
    id: int
    file_name: str
    file_size: int
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    status: int
    sync_status: int
    sync_error: Optional[str] = None
    synced_at: Optional[datetime] = None
    created_by: int
    embedding_id: Optional[str] = None
    embedding_info: Optional[Dict[str, Any]] = None
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeDocListResponse(BaseModel):
    items: List[KnowledgeDocResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeDocChunkResponse(BaseModel):
    id: int
    doc_id: int
    chunk_index: Optional[int] = None
    chunk_content: Optional[str] = None
    chunk_hash: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    char_count: Optional[int] = None
    token_count: Optional[int] = None
    hermes_embedding_id: Optional[str] = None
    embedding_info: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class SyncStatusResponse(BaseModel):
    doc_id: int
    sync_status: int
    synced_at: Optional[datetime] = None
    message: str


class UploadResult(BaseModel):
    doc: KnowledgeDocResponse
    sync_status: int
    message: str = "上传成功"


class DeleteResult(BaseModel):
    success: bool
    message: str
