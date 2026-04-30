from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class AgentTemplateBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100, description="模板编码（英文唯一标识）")
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    template_type: str = Field("business", description="模板类型：business-业务模板，system-系统模板")
    role_prompt: Optional[str] = Field(None, description="角色说明提示词")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    welcome_message: Optional[str] = Field(None, description="欢迎语")
    knowledge_scope: str = Field("category", description="知识范围类型：none/global/category/custom")
    knowledge_categories: Optional[List[str]] = Field(default_factory=list, description="知识分类列表")
    tool_policy: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工具策略")
    output_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="输出规则")
    confirmation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="确认规则")
    interaction_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="交互规则")
    workflow_hints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="流程提示")
    model_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模型配置")
    is_default: bool = Field(False, description="是否为默认模板")


class AgentTemplateCreate(AgentTemplateBase):
    pass


class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    template_type: Optional[str] = None
    role_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    knowledge_scope: Optional[str] = None
    knowledge_categories: Optional[List[str]] = None
    tool_policy: Optional[Dict[str, Any]] = None
    output_rules: Optional[Dict[str, Any]] = None
    confirmation_rules: Optional[Dict[str, Any]] = None
    interaction_rules: Optional[Dict[str, Any]] = None
    workflow_hints: Optional[Dict[str, Any]] = None
    model_settings: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    status: Optional[int] = None


class AgentTemplateResponse(AgentTemplateBase):
    id: int
    status: int = Field(0, description="模板状态：0-草稿，1-启用，2-停用")
    version: int = Field(1, description="当前版本号")
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentTemplateListResponse(BaseModel):
    items: List[AgentTemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentTemplateVersionResponse(BaseModel):
    id: int
    template_id: int
    version_no: int
    version_label: Optional[str] = None
    change_summary: Optional[str] = None
    template_snapshot: Dict[str, Any]
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PublishTemplateRequest(BaseModel):
    version_label: Optional[str] = Field(None, max_length=100, description="版本标签")
    change_summary: Optional[str] = Field(None, max_length=1000, description="变更说明")


class SyncTemplateRequest(BaseModel):
    sync_mode: str = Field("all_enabled_users", description="同步模式：all_enabled_users/selected_users")
    user_ids: Optional[List[int]] = Field(default_factory=list, description="指定用户ID列表")
