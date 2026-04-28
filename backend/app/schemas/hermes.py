from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"


class HermesSystemInfo(BaseModel):
    version: str = Field(..., description="Hermes 当前版本号")
    latest_version: Optional[str] = Field(None, description="最新可用版本号")
    has_update: bool = Field(False, description="是否有可用更新")
    status: HealthStatus = Field(..., description="系统运行状态")
    uptime: str = Field(..., description="运行时长")
    start_time: Optional[datetime] = Field(None, description="启动时间")
    api_server_port: Optional[int] = Field(None, description="API Server 端口")


class HermesStatistics(BaseModel):
    total_profiles: int = Field(0, description="总 Profile 数量")
    running_profiles: int = Field(0, description="运行中的 Profile 数量")
    stopped_profiles: int = Field(0, description="已停止的 Profile 数量")
    total_users: int = Field(0, description="总用户数")
    today_conversations: int = Field(0, description="今日对话数")
    total_conversations: int = Field(0, description="总对话数")
    total_skills: int = Field(0, description="总技能数")
    total_mcp_services: int = Field(0, description="总 MCP 服务数")
    total_documents: int = Field(0, description="总文档数")


class HealthCheckItem(BaseModel):
    name: str = Field(..., description="检查项名称")
    status: HealthStatus = Field(..., description="状态")
    message: str = Field(..., description="详细信息")
    value: Optional[str] = Field(None, description="当前值")


class HermesHealthStatus(BaseModel):
    overall: HealthStatus = Field(..., description="整体健康状态")
    items: List[HealthCheckItem] = Field(default_factory=list, description="各检查项详情")
    checked_at: datetime = Field(default_factory=datetime.now, description="检查时间")


class RecentActivity(BaseModel):
    time: str = Field(..., description="时间")
    user_name: str = Field(..., description="用户名")
    event: str = Field(..., description="事件类型")
    details: Optional[str] = Field(None, description="详情")


class HermesOverviewResponse(BaseModel):
    system_info: HermesSystemInfo = Field(..., description="系统信息")
    statistics: HermesStatistics = Field(..., description="统计信息")
    health_status: HermesHealthStatus = Field(..., description="健康状态")
    recent_activities: List[RecentActivity] = Field(default_factory=list, description="最近活动")


class VersionCheckResponse(BaseModel):
    current_version: str = Field(..., description="当前版本")
    latest_version: str = Field(..., description="最新版本")
    has_update: bool = Field(..., description="是否有更新")
    changelog: Optional[str] = Field(None, description="更新日志")
    release_url: Optional[str] = Field(None, description="发布页面 URL")


class UpdateProgress(BaseModel):
    status: str = Field(..., description="更新状态: checking, downloading, installing, completed, failed")
    progress: int = Field(0, description="进度百分比 0-100")
    message: str = Field(..., description="当前操作消息")
    error: Optional[str] = Field(None, description="错误信息")
