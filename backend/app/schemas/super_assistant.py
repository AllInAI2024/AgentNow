from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SuperAssistantMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="消息角色")
    content: str = Field("", description="消息内容")
    ts: float = Field(..., description="时间戳（秒）")


class SuperAssistantSession(BaseModel):
    session_id: str = Field(..., description="Hermes 会话ID（对应 Profile 下 state.db.sessions.id）")
    title: str = Field("Untitled", description="会话标题")
    profile: str = Field(..., description="Hermes Profile")
    hermes_session_id: Optional[str] = Field(None, description="兼容字段：同 session_id")
    hermes_response_id: Optional[str] = Field(None, description="Hermes Responses API 的 response_id（HTTP API 模式）")
    model: Optional[str] = Field(None, description="会话选择的模型")
    reasoning_effort: Optional[str] = Field(None, description="思考级别：none/minimal/low/medium/high/xhigh")
    show_reasoning: Optional[bool] = Field(None, description="是否显示思考内容（如果 Hermes 支持）")
    created_at: float = Field(..., description="创建时间戳（秒）")
    updated_at: float = Field(..., description="更新时间戳（秒）")
    message_count: int = Field(0, description="消息数量")
    messages: List[SuperAssistantMessage] = Field(default_factory=list, description="消息列表")


class SuperAssistantSessionListItem(BaseModel):
    session_id: str
    title: str
    profile: str
    created_at: float
    updated_at: float
    message_count: int
    last_message_at: Optional[float] = None


class SuperAssistantSessionListResponse(BaseModel):
    items: List[SuperAssistantSessionListItem] = Field(default_factory=list)


class SuperAssistantNewSessionRequest(BaseModel):
    title: Optional[str] = Field(None, description="可选：初始标题")


class SuperAssistantChatStartRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Hermes 会话ID；为空则创建新会话")
    message: str = Field(..., min_length=1, description="用户消息")
    workspace: Optional[str] = Field(None, description="工作区路径；为空则使用上次选择/默认工作区")
    model: Optional[str] = Field(None, description="选择的模型（可选）")
    reasoning_effort: Optional[str] = Field(None, description="思考级别（可选）")
    show_reasoning: Optional[bool] = Field(None, description="是否显示思考（可选）")
    attachments: Optional[list[dict]] = Field(None, description="附件列表（由上传接口返回的对象数组）")


class SuperAssistantChatStartResponse(BaseModel):
    stream_id: str = Field(..., description="流ID（用于 SSE）")


class SuperAssistantDeleteSessionRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")


class SuperAssistantModelListItem(BaseModel):
    id: str = Field(..., description="模型ID")


class SuperAssistantModelListResponse(BaseModel):
    models: List[SuperAssistantModelListItem] = Field(default_factory=list)


class SuperAssistantUploadResponse(BaseModel):
    name: str
    path: str
    mime: Optional[str] = None
    size: int = 0
    is_image: bool = False


class SuperAssistantWorkspaceItem(BaseModel):
    name: str
    path: str


class SuperAssistantWorkspaceListResponse(BaseModel):
    items: List[SuperAssistantWorkspaceItem] = Field(default_factory=list)
    current: str = Field("", description="当前工作区路径")
    default: str = Field("", description="默认工作区路径（Profile 目录）")


class SuperAssistantWorkspaceSelectRequest(BaseModel):
    path: str = Field(..., min_length=1, description="工作区路径")
