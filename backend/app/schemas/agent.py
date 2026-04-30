from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class UserAgentBase(BaseModel):
    template_id: int = Field(..., description="绑定的模板ID")
    display_name: Optional[str] = Field(None, max_length=100, description="智能体显示名称")


class UserAgentResponse(BaseModel):
    id: int
    user_id: int
    template_id: int
    display_name: str
    hermes_profile: str
    template_version: int
    config_snapshot: Optional[Dict[str, Any]] = None
    agent_status: int = Field(1, description="智能体状态：0-待开通，1-可用，2-已停用，3-开通失败")
    activation_mode: Optional[str] = None
    enabled_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAgentWithTemplateResponse(UserAgentResponse):
    template: Optional[Dict[str, Any]] = None


class UserAgentListResponse(BaseModel):
    items: List[UserAgentWithTemplateResponse]
    total: int


class EnableAgentRequest(BaseModel):
    template_id: Optional[int] = Field(None, description="模板ID（不传则使用默认模板）")


class EnableAgentResponse(BaseModel):
    user_agent: UserAgentResponse
    created_profile: bool = Field(False, description="是否创建了新的Hermes Profile")


class AgentConversationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="会话标题")


class AgentConversationResponse(BaseModel):
    id: int
    user_id: int
    user_agent_id: int
    hermes_profile: str
    hermes_conversation_id: Optional[str] = None
    hermes_response_id: Optional[str] = None
    title: Optional[str] = None
    current_stage: str = Field("chatting", description="当前阶段")
    status: int = Field(1, description="会话状态：0-草稿，1-进行中，2-已完成，3-已归档，4-失败")
    outline_confirmed: bool = False
    template_confirmed: bool = False
    final_generation_confirmed: bool = False
    message_count: int = 0
    latest_user_input: Optional[str] = None
    final_file_id: Optional[int] = None
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentConversationListResponse(BaseModel):
    items: List[AgentConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = Field(None, description="会话ID（不传表示新建会话）")
    message: Optional[str] = Field(None, description="用户输入文本")
    action_type: str = Field("message", description="动作类型：message/confirm_outline/revise_outline/confirm_template/confirm_generation/revise_content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="辅助元数据")


class ChatResponse(BaseModel):
    conversation: AgentConversationResponse
    assistant_message: Optional[Dict[str, Any]] = None
    structured_result: Optional[Dict[str, Any]] = None


class ConversationDetailResponse(BaseModel):
    conversation: AgentConversationResponse
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    structured_result: Optional[Dict[str, Any]] = None
    files: List[Dict[str, Any]] = Field(default_factory=list)


class AgentGeneratedFileResponse(BaseModel):
    id: int
    user_id: int
    user_agent_id: int
    conversation_id: Optional[int] = None
    file_type: str
    file_name: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    template_name: Optional[str] = None
    source_type: Optional[str] = None
    version_no: int = 1
    generation_status: int = Field(1, description="生成状态：0-生成中，1-成功，2-失败")
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GeneratePPTRequest(BaseModel):
    conversation_id: int = Field(..., description="会话ID")
    template_name: Optional[str] = Field(None, max_length=100, description="模板名称")
    regenerate: bool = Field(False, description="是否为重新生成")


class AgentOperationLogResponse(BaseModel):
    id: int
    operator_user_id: int
    target_type: str
    target_id: Optional[int] = None
    action: str
    action_name: Optional[str] = None
    result_status: int
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentOperationLogListResponse(BaseModel):
    items: List[AgentOperationLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
