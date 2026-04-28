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


class HermesSkillMetadata(BaseModel):
    tags: Optional[List[str]] = Field(default_factory=list, description="技能标签")
    related_skills: Optional[List[str]] = Field(default_factory=list, description="相关技能列表")


class SkillMetadata(BaseModel):
    hermes: Optional[HermesSkillMetadata] = Field(default=None, description="Hermes 元数据")


class Skill(BaseModel):
    name: str = Field(..., description="技能名称")
    description: Optional[str] = Field(None, description="技能描述")
    version: Optional[str] = Field(None, description="技能版本")
    author: Optional[str] = Field(None, description="作者")
    license: Optional[str] = Field(None, description="许可证")
    metadata: Optional[SkillMetadata] = Field(default=None, description="元数据")
    content: Optional[str] = Field(None, description="SKILL.md 完整内容")
    category: Optional[str] = Field(None, description="技能分类（目录名）")
    path: Optional[str] = Field(None, description="技能文件路径")
    is_bundled: bool = Field(False, description="是否为内置技能")
    is_installed: bool = Field(True, description="是否已安装")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    usage_count: int = Field(0, description="使用次数统计")


class SkillCategory(BaseModel):
    name: str = Field(..., description="分类名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="分类描述")
    skill_count: int = Field(0, description="该分类下的技能数量")


class SkillListResponse(BaseModel):
    items: List[Skill] = Field(default_factory=list, description="技能列表")
    total: int = Field(0, description="总数量")
    categories: List[SkillCategory] = Field(default_factory=list, description="所有分类")
    bundled_count: int = Field(0, description="内置技能数量")
    installed_count: int = Field(0, description="已安装技能数量")


class SkillInstallParams(BaseModel):
    identifier: str = Field(..., description="技能标识符（如 openai/skills/skill-creator）或 SKILL.md URL")
    name: Optional[str] = Field(None, description="覆盖技能名称（从 URL 安装时使用）")
    category: Optional[str] = Field(None, description="安装到的分类目录")
    force: bool = Field(False, description="忽略扫描结果强制安装")


class SkillCreateParams(BaseModel):
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    version: str = Field("1.0.0", description="技能版本")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    content: str = Field(..., description="SKILL.md 内容（包含 frontmatter）")
    category: Optional[str] = Field("custom", description="分类目录")


class SkillDetailResponse(BaseModel):
    skill: Skill = Field(..., description="技能详细信息")
    has_update: bool = Field(False, description="是否有更新")
    latest_version: Optional[str] = Field(None, description="最新版本")
