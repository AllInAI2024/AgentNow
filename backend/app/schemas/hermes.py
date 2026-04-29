from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"


class SkillType(str, Enum):
    BUNDLED = "bundled"
    COMMUNITY = "community"
    AGENT_CREATED = "agent_created"
    USER_UPLOADED = "user_uploaded"


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
    skill_type: SkillType = Field(SkillType.BUNDLED, description="技能类型：bundled/community/agent_created/user_uploaded")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    usage_count: int = Field(0, description="使用次数统计")


class SkillCategory(BaseModel):
    name: str = Field(..., description="分类名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="分类描述")
    skill_count: int = Field(0, description="该分类下的技能总数")
    installed_count: int = Field(0, description="该分类下已安装的技能数量")


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
    skill_type: SkillType = Field(SkillType.AGENT_CREATED, description="技能类型：agent_created/user_uploaded")


class SkillDetailResponse(BaseModel):
    skill: Skill = Field(..., description="技能详细信息")
    has_update: bool = Field(False, description="是否有更新")
    latest_version: Optional[str] = Field(None, description="最新版本")


class MCPTool(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Optional[dict] = Field(None, description="输入参数 schema")


class MCPService(BaseModel):
    name: str = Field(..., description="服务名称")
    type: str = Field(..., description="服务类型: stdio 或 sse")
    type_display: str = Field(..., description="类型显示名称")
    status: HealthStatus = Field(..., description="服务状态")
    command: Optional[str] = Field(None, description="启动命令（stdio 类型）")
    args: Optional[List[str]] = Field(None, description="命令参数")
    url: Optional[str] = Field(None, description="SSE 服务 URL（SSE 类型）")
    tool_count: int = Field(0, description="提供的工具数量")
    tools: List[MCPTool] = Field(default_factory=list, description="工具列表")
    last_check: Optional[datetime] = Field(None, description="最后检查时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    config_raw: Optional[str] = Field(None, description="原始配置（用于编辑）")


class MCPServiceListResponse(BaseModel):
    items: List[MCPService] = Field(default_factory=list, description="MCP 服务列表")
    total: int = Field(0, description="总数量")
    running_count: int = Field(0, description="运行中数量")
    warning_count: int = Field(0, description="警告数量")
    stopped_count: int = Field(0, description="已停止数量")


class MCPServiceDetailResponse(BaseModel):
    service: MCPService = Field(..., description="服务详细信息")


class MCPServiceTestResult(BaseModel):
    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    tool_count: Optional[int] = Field(None, description="检测到的工具数量")
    tools: List[MCPTool] = Field(default_factory=list, description="检测到的工具列表")
    error: Optional[str] = Field(None, description="错误信息")


class BuiltinToolParameter(BaseModel):
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必填")
    default: Optional[str] = Field(None, description="默认值")


class BuiltinTool(BaseModel):
    name: str = Field(..., description="工具名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="工具描述")
    category: str = Field(..., description="工具分类")
    parameters: List[BuiltinToolParameter] = Field(default_factory=list, description="参数列表")
    return_description: Optional[str] = Field(None, description="返回值描述")
    examples: List[str] = Field(default_factory=list, description="使用示例")
    notes: Optional[str] = Field(None, description="使用注意事项")


class BuiltinToolCategory(BaseModel):
    name: str = Field(..., description="分类名称")
    display_name: str = Field(..., description="显示名称")
    icon: str = Field(..., description="图标")
    description: str = Field(..., description="分类描述")
    tool_count: int = Field(0, description="工具数量")


class BuiltinToolListResponse(BaseModel):
    categories: List[BuiltinToolCategory] = Field(default_factory=list, description="工具分类列表")
    tools: List[BuiltinTool] = Field(default_factory=list, description="所有工具列表")
    total_tools: int = Field(0, description="工具总数")


class MemoryType(str, Enum):
    MEMORY = "memory"
    USER = "user"


class MemoryItem(BaseModel):
    id: int = Field(..., description="条目索引")
    type: str = Field(..., description="条目类型：环境事实、用户偏好、项目约定等")
    content: str = Field(..., description="条目内容")
    raw: str = Field(..., description="原始文本行")
    line_number: int = Field(..., description="在文件中的行号")


class MemoryFile(BaseModel):
    type: MemoryType = Field(..., description="记忆文件类型")
    name: str = Field(..., description="文件名：MEMORY.md 或 USER.md")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="文件用途描述")
    char_limit: int = Field(..., description="字符限制")
    current_chars: int = Field(0, description="当前字符数")
    progress: float = Field(0.0, description="使用进度百分比 (0-100)")
    item_count: int = Field(0, description="条目数量")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    exists: bool = Field(False, description="文件是否存在")
    raw_content: Optional[str] = Field(None, description="原始文件内容")
    items: List[MemoryItem] = Field(default_factory=list, description="解析后的记忆条目列表")


class MemoryResponse(BaseModel):
    profile_name: str = Field(..., description="Profile 名称")
    memory_file: MemoryFile = Field(..., description="MEMORY.md (Agent 笔记)")
    user_file: MemoryFile = Field(..., description="USER.md (用户画像)")


class ProfileMemoryListItem(BaseModel):
    profile_name: str = Field(..., description="Profile 名称")
    display_name: str = Field(..., description="显示名称（如用户名）")
    user_id: Optional[int] = Field(None, description="关联用户ID")
    user_name: Optional[str] = Field(None, description="关联用户名")
    memory_exists: bool = Field(False, description="MEMORY.md 是否存在")
    user_exists: bool = Field(False, description="USER.md 是否存在")
    memory_chars: int = Field(0, description="MEMORY.md 当前字符数")
    user_chars: int = Field(0, description="USER.md 当前字符数")
    memory_limit: int = Field(2200, description="MEMORY.md 字符限制")
    user_limit: int = Field(1375, description="USER.md 字符限制")


class ProfileMemoryListResponse(BaseModel):
    items: List[ProfileMemoryListItem] = Field(default_factory=list, description="Profile 记忆列表")
    total: int = Field(0, description="总数量")


class ConfigItem(BaseModel):
    key: str = Field(..., description="配置项键名")
    value: Optional[str] = Field(None, description="配置项值（已脱敏）")
    display_value: Optional[str] = Field(None, description="显示值（已脱敏处理）")
    description: Optional[str] = Field(None, description="配置项描述")
    category: str = Field(..., description="配置分类")
    is_sensitive: bool = Field(False, description="是否为敏感配置")
    is_editable: bool = Field(False, description="是否可编辑")
    source: str = Field("config.yaml", description="配置来源: config.yaml 或 .env")


class ConfigCategory(str, Enum):
    MODEL = "model"
    TERMINAL = "terminal"
    API_SERVER = "api_server"
    MEMORY = "memory"
    COMPRESSION = "compression"
    TOOLS = "tools"
    GENERAL = "general"


class ModelConfig(BaseModel):
    default_model: Optional[str] = Field(None, description="默认模型")
    model_provider: Optional[str] = Field(None, description="模型提供商")
    context_window: Optional[int] = Field(None, description="上下文窗口大小(tokens)")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大输出tokens")


class TerminalConfig(BaseModel):
    backend: Optional[str] = Field(None, description="终端后端: local/docker/ssh/modal/daytona/singularity")
    cwd: Optional[str] = Field(None, description="工作目录")
    timeout: Optional[int] = Field(None, description="命令超时时间(秒)")
    env_passthrough: List[str] = Field(default_factory=list, description="允许传递的环境变量")


class APIServerConfig(BaseModel):
    enabled: bool = Field(False, description="是否启用API Server")
    port: Optional[int] = Field(None, description="服务端口")
    host: Optional[str] = Field(None, description="绑定地址")
    cors_origins: List[str] = Field(default_factory=list, description="CORS允许的来源")
    model_name: Optional[str] = Field(None, description="模型名称显示")


class MemoryConfig(BaseModel):
    memory_char_limit: int = Field(2200, description="MEMORY.md字符限制")
    user_char_limit: int = Field(1375, description="USER.md字符限制")
    auto_save: bool = Field(True, description="是否自动保存记忆")


class CompressionConfig(BaseModel):
    enabled: bool = Field(True, description="是否启用压缩")
    strategy: Optional[str] = Field(None, description="压缩策略")
    threshold_tokens: Optional[int] = Field(None, description="触发压缩的token阈值")


class ToolsConfig(BaseModel):
    enabled_tools: List[str] = Field(default_factory=list, description="启用的工具列表")
    disabled_tools: List[str] = Field(default_factory=list, description="禁用的工具列表")


class GeneralConfig(BaseModel):
    log_level: Optional[str] = Field(None, description="日志级别")
    auto_update: bool = Field(False, description="是否自动更新")
    telemetry_enabled: bool = Field(True, description="是否启用遥测")


class ConfigResponse(BaseModel):
    profile_name: str = Field("global", description="Profile名称，global表示全局配置")
    model: ModelConfig = Field(default_factory=ModelConfig, description="模型配置")
    terminal: TerminalConfig = Field(default_factory=TerminalConfig, description="终端配置")
    api_server: APIServerConfig = Field(default_factory=APIServerConfig, description="API Server配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="记忆配置")
    compression: CompressionConfig = Field(default_factory=CompressionConfig, description="压缩配置")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="工具配置")
    general: GeneralConfig = Field(default_factory=GeneralConfig, description="通用配置")
    raw_config: Optional[str] = Field(None, description="原始配置内容（仅供调试，敏感信息已脱敏）")
    config_file_path: Optional[str] = Field(None, description="配置文件路径")
    env_file_path: Optional[str] = Field(None, description="环境变量文件路径")
    last_updated: Optional[datetime] = Field(None, description="配置最后更新时间")


class ConfigUpdateRequest(BaseModel):
    category: str = Field(..., description="配置分类")
    key: str = Field(..., description="配置项键名")
    value: str = Field(..., description="配置值")


class ConfigUpdateResponse(BaseModel):
    success: bool = Field(..., description="是否更新成功")
    message: str = Field(..., description="结果消息")
    updated_key: Optional[str] = Field(None, description="更新的配置项")


class ConfigProfileItem(BaseModel):
    name: str = Field(..., description="Profile名称")
    display_name: str = Field(..., description="显示名称")
    has_config: bool = Field(True, description="是否有配置文件")
    is_global: bool = Field(False, description="是否为全局配置")


class ConfigProfileListResponse(BaseModel):
    items: List[ConfigProfileItem] = Field(default_factory=list, description="Profile列表")
    total: int = Field(0, description="总数量")


class HermesKnowledgeDocStatus(str, Enum):
    INDEXED = "indexed"
    INDEXING = "indexing"
    FAILED = "failed"
    PENDING = "pending"


class HermesKnowledgeDoc(BaseModel):
    id: str = Field(..., description="文档ID（文件路径哈希或相对路径）")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="相对存储路径")
    file_size: int = Field(0, description="文件大小（字节）")
    file_type: Optional[str] = Field(None, description="文件类型/扩展名")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    word_count: int = Field(0, description="字数统计（仅文本文件）")
    char_count: int = Field(0, description="字符数")
    title: Optional[str] = Field(None, description="文档标题（从Frontmatter或内容提取）")
    description: Optional[str] = Field(None, description="文档描述/摘要")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, description="文档分类（目录结构）")
    status: HermesKnowledgeDocStatus = Field(HermesKnowledgeDocStatus.INDEXED, description="索引状态")
    created_at: datetime = Field(default_factory=datetime.now, description="文件创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="文件最后修改时间")
    last_indexed_at: Optional[datetime] = Field(None, description="最后索引时间")


class HermesKnowledgeDocDetail(HermesKnowledgeDoc):
    content: Optional[str] = Field(None, description="文档内容（仅文本文件）")
    frontmatter: Optional[dict] = Field(None, description="YAML Frontmatter数据")
    outline: Optional[List[dict]] = Field(None, description="文档大纲（标题结构）")


class HermesKnowledgeStatus(BaseModel):
    status: HealthStatus = Field(HealthStatus.HEALTHY, description="知识库整体状态")
    total_docs: int = Field(0, description="总文档数")
    total_chars: int = Field(0, description="总字符数")
    total_size: int = Field(0, description="总文件大小（字节）")
    indexed_docs: int = Field(0, description="已索引文档数")
    pending_docs: int = Field(0, description="待索引文档数")
    failed_docs: int = Field(0, description="索引失败文档数")
    last_index_at: Optional[datetime] = Field(None, description="最后索引时间")
    index_engine: str = Field("Hermes RAG", description="索引引擎名称")
    storage_path: str = Field(..., description="知识库存储路径")


class HermesKnowledgeListResponse(BaseModel):
    items: List[HermesKnowledgeDoc] = Field(default_factory=list, description="文档列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
    categories: List[str] = Field(default_factory=list, description="所有分类")


class HermesKnowledgeStatusResponse(BaseModel):
    status: HermesKnowledgeStatus = Field(..., description="知识库状态")


class HermesAuditLog(BaseModel):
    id: int = Field(..., description="审计日志ID")
    user_id: int = Field(..., description="操作人ID")
    user_name: str = Field(..., description="操作人名称")
    action: str = Field(..., description="操作类型标识")
    action_name: str = Field(..., description="操作类型名称")
    target_type: Optional[str] = Field(None, description="目标类型")
    target_id: Optional[str] = Field(None, description="目标ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作时间")


class HermesAuditLogListResponse(BaseModel):
    items: List[HermesAuditLog] = Field(default_factory=list, description="审计日志列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
