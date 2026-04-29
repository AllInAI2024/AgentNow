export interface User {
  id: number
  department_id: number | null
  login_name: string
  phone: string | null
  email: string | null
  username: string
  avatar_url: string | null
  hermes_profile: string | null
  hermes_profile_config: string | null
  is_active: boolean
  is_default_password: boolean
  is_super_admin: boolean
  last_login_at: string | null
  last_login_ip: string | null
  password_changed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface Department {
  id: number
  parent_id: number
  name: string
  code: string | null
  description: string | null
  sort: number
  status: number
  leader_id: number | null
  created_at: string | null
  updated_at: string | null
}

export interface DepartmentTree extends Department {
  children: DepartmentTree[]
}

export interface LoginParams {
  login_name: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  user: User
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export interface CreateEmployeeParams {
  department_id: number
  login_name: string
  username: string
  phone?: string
  email?: string
  password?: string
  avatar_url?: string
  hermes_profile?: string
  hermes_profile_config?: string
}

export interface UpdateEmployeeParams {
  department_id?: number
  username?: string
  phone?: string
  email?: string
  avatar_url?: string
  hermes_profile?: string
  hermes_profile_config?: string
  is_active?: boolean
}

export interface CreateDepartmentParams {
  parent_id: number
  name: string
  code?: string
  description?: string
  sort?: number
  status?: number
  leader_id?: number
}

export interface UpdateDepartmentParams {
  parent_id?: number
  name?: string
  code?: string
  description?: string
  sort?: number
  status?: number
  leader_id?: number
}

export interface APIResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface Permission {
  id: number
  parent_id: number
  name: string
  code: string
  type: number
  path: string | null
  icon: string | null
  sort: number
  divider: boolean
  created_at: string | null
  updated_at: string | null
}

export interface PermissionTree extends Permission {
  children: PermissionTree[]
}

export interface Role {
  id: number
  name: string
  code: string
  description: string | null
  created_at: string | null
  updated_at: string | null
}

export interface KnowledgeDoc {
  id: number
  title: string
  file_name: string
  file_path: string
  file_size: number
  file_type: string | null
  mime_type: string | null
  content_hash: string | null
  description: string | null
  tags: string[]
  category: string | null
  created_by: number
  updated_by: number | null
  is_public: boolean
  word_count: number | null
  file_modified_at: string | null
  deleted_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface KnowledgeDocDetail extends KnowledgeDoc {
  content?: string
}

export interface KnowledgeDocList {
  items: KnowledgeDoc[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CreateKnowledgeDocParams {
  title: string
  description?: string
  tags?: string[]
  category?: string
  is_public?: boolean
}

export interface UpdateKnowledgeDocParams {
  title?: string
  description?: string
  tags?: string[]
  category?: string
  is_public?: boolean
}

export interface UpdateKnowledgeDocContentParams {
  content: string
}

export interface KnowledgeConfig {
  id: number
  config_key: string
  config_value: string
  description: string | null
  created_at: string | null
  updated_at: string | null
}

export interface DeleteResult {
  success: boolean
  message: string
}

export interface UploadResult {
  doc: KnowledgeDoc
  message: string
}

export interface AllTagsResponse {
  tags: string[]
  total: number
}

export interface AllCategoriesResponse {
  categories: string[]
  total: number
}

export interface FileSystemInfo {
  base_path: string
  total_files: number
  total_size: number
  free_space: number
}

export interface StatisticsResponse {
  total_docs: number
  total_size: number
  total_categories: number
  total_tags: number
  public_docs: number
  recent_uploads: number
}

export type HealthStatus = 'healthy' | 'unhealthy' | 'warning'

export type SkillType = 'bundled' | 'community' | 'agent_created' | 'user_uploaded'

export interface HermesSystemInfo {
  version: string
  latest_version: string | null
  has_update: boolean
  status: HealthStatus
  uptime: string
  start_time: string | null
  api_server_port: number | null
}

export interface HermesStatistics {
  total_profiles: number
  running_profiles: number
  stopped_profiles: number
  total_users: number
  today_conversations: number
  total_conversations: number
  total_skills: number
  total_mcp_services: number
  total_documents: number
}

export interface HealthCheckItem {
  name: string
  status: HealthStatus
  message: string
  value: string | null
}

export interface HermesHealthStatus {
  overall: HealthStatus
  items: HealthCheckItem[]
  checked_at: string
}

export interface RecentActivity {
  time: string
  user_name: string
  event: string
  details: string | null
}

export interface HermesOverviewResponse {
  system_info: HermesSystemInfo
  statistics: HermesStatistics
  health_status: HermesHealthStatus
  recent_activities: RecentActivity[]
}

export interface VersionCheckResponse {
  current_version: string
  latest_version: string
  has_update: boolean
  changelog: string | null
  release_url: string | null
}

export interface UpdateProgress {
  status: 'checking' | 'downloading' | 'installing' | 'completed' | 'failed'
  progress: number
  message: string
  error: string | null
}

export interface HermesSkillMetadata {
  tags: string[]
  related_skills: string[]
}

export interface SkillMetadata {
  hermes: HermesSkillMetadata
}

export interface Skill {
  name: string
  description: string
  version: string
  author: string
  license: string
  metadata: SkillMetadata
  content: string
  category: string
  category_name: string
  path: string
  is_bundled: boolean
  is_installed: boolean
  skill_type: SkillType
  created_at: string | null
  updated_at: string | null
  usage_count: number
}

export interface SkillCategory {
  name: string
  display_name: string
  skill_count: number
  installed_count: number
}

export interface SkillListResponse {
  total: number
  categories: SkillCategory[]
  items: Skill[]
  bundled_count: number
  installed_count: number
}

export interface SkillDetailResponse extends Skill {
  description_html: string | null
}

export interface SkillInstallParams {
  identifier: string
  name?: string
  category?: string
  force?: boolean
}

export interface SkillCreateParams {
  name: string
  description: string
  content: string
  category?: string
  version?: string
  author?: string
  license?: string
  tags?: string[]
  skill_type?: SkillType
}

export interface AvailableSkill {
  name: string
  description: string
  source: string
  trust: string
  identifier: string
  is_installed: boolean
}

export interface MCPTool {
  name: string
  description: string
  input_schema?: Record<string, any>
}

export interface MCPService {
  name: string
  type: 'stdio' | 'sse'
  type_display: string
  status: HealthStatus
  command?: string
  args?: string[]
  url?: string
  tool_count: number
  tools: MCPTool[]
  last_check?: string
  error_message?: string
  config_raw?: string
}

export interface MCPServiceListResponse {
  items: MCPService[]
  total: number
  running_count: number
  warning_count: number
  stopped_count: number
}

export interface MCPServiceDetailResponse {
  service: MCPService
}

export interface MCPServiceTestResult {
  success: boolean
  message: string
  tool_count?: number
  tools: MCPTool[]
  error?: string
}

export interface BuiltinToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default: string | null
}

export interface BuiltinTool {
  name: string
  display_name: string
  description: string
  category: string
  parameters: BuiltinToolParameter[]
  return_description: string | null
  examples: string[]
  notes: string | null
}

export interface BuiltinToolCategory {
  name: string
  display_name: string
  icon: string
  description: string
  tool_count: number
}

export interface BuiltinToolListResponse {
  categories: BuiltinToolCategory[]
  tools: BuiltinTool[]
  total_tools: number
}

export type MemoryType = 'memory' | 'user'

export interface MemoryItem {
  id: number
  type: string
  content: string
  raw: string
  line_number: number
}

export interface MemoryFile {
  type: MemoryType
  name: string
  display_name: string
  description: string
  char_limit: number
  current_chars: number
  progress: number
  item_count: number
  last_updated: string | null
  exists: boolean
  raw_content: string | null
  items: MemoryItem[]
}

export interface MemoryResponse {
  profile_name: string
  memory_file: MemoryFile
  user_file: MemoryFile
}

export interface ProfileMemoryListItem {
  profile_name: string
  display_name: string
  user_id: number | null
  user_name: string | null
  memory_exists: boolean
  user_exists: boolean
  memory_chars: number
  user_chars: number
  memory_limit: number
  user_limit: number
}

export interface ProfileMemoryListResponse {
  items: ProfileMemoryListItem[]
  total: number
}

export interface ConfigProfileItem {
  name: string
  display_name: string
  has_config: boolean
  is_global: boolean
}

export interface ConfigProfileListResponse {
  items: ConfigProfileItem[]
  total: number
}

export interface ModelConfig {
  default_model: string | null
  model_provider: string | null
  context_window: number | null
  temperature: number | null
  max_tokens: number | null
}

export interface TerminalConfig {
  backend: string | null
  cwd: string | null
  timeout: number | null
  env_passthrough: string[]
}

export interface APIServerConfig {
  enabled: boolean
  port: number | null
  host: string | null
  cors_origins: string[]
  model_name: string | null
}

export interface MemoryConfig {
  memory_char_limit: number
  user_char_limit: number
  auto_save: boolean
}

export interface CompressionConfig {
  enabled: boolean
  strategy: string | null
  threshold_tokens: number | null
}

export interface ToolsConfig {
  enabled_tools: string[]
  disabled_tools: string[]
}

export interface GeneralConfig {
  log_level: string | null
  auto_update: boolean
  telemetry_enabled: boolean
}

export interface ConfigResponse {
  profile_name: string
  model: ModelConfig
  terminal: TerminalConfig
  api_server: APIServerConfig
  memory: MemoryConfig
  compression: CompressionConfig
  tools: ToolsConfig
  general: GeneralConfig
  raw_config: string | null
  config_file_path: string | null
  env_file_path: string | null
  last_updated: string | null
}

export type HermesKnowledgeDocStatus = 'indexed' | 'indexing' | 'failed' | 'pending'

export interface HermesKnowledgeDoc {
  id: string
  file_name: string
  file_path: string
  file_size: number
  file_type: string | null
  mime_type: string | null
  word_count: number
  char_count: number
  title: string | null
  description: string | null
  tags: string[]
  category: string | null
  status: HermesKnowledgeDocStatus
  created_at: string
  updated_at: string
  last_indexed_at: string | null
}

export interface HermesKnowledgeDocDetail extends HermesKnowledgeDoc {
  content: string | null
  frontmatter: Record<string, any> | null
  outline: OutlineItem[] | null
}

export interface OutlineItem {
  level: number
  title: string
  line_number: number
}

export interface HermesKnowledgeStatus {
  status: HealthStatus
  total_docs: number
  total_chars: number
  total_size: number
  indexed_docs: number
  pending_docs: number
  failed_docs: number
  last_index_at: string | null
  index_engine: string
  storage_path: string
}

export interface HermesKnowledgeListResponse {
  items: HermesKnowledgeDoc[]
  total: number
  page: number
  page_size: number
  total_pages: number
  categories: string[]
}

export interface FileTypeStat {
  type: string
  count: number
}

export interface HermesAuditLog {
  id: number
  user_id: number
  user_name: string
  action: string
  action_name: string
  target_type?: string
  target_id?: string
  details: Record<string, unknown>
  ip_address: string
  user_agent: string
  timestamp: string
}

export const HermesActionType = {
  VIEW_OVERVIEW: 'hermes:view:overview',
  VIEW_PROFILES: 'hermes:view:profiles',
  VIEW_PROFILE_DETAIL: 'hermes:view:profile_detail',
  VIEW_CONVERSATIONS: 'hermes:view:conversations',
  VIEW_CONVERSATION_DETAIL: 'hermes:view:conversation_detail',
  VIEW_SKILLS: 'hermes:view:skills',
  VIEW_MCP: 'hermes:view:mcp',
  VIEW_TOOLS: 'hermes:view:tools',
  VIEW_MEMORY: 'hermes:view:memory',
  VIEW_CONFIG: 'hermes:view:config',
  VIEW_KNOWLEDGE: 'hermes:view:knowledge',
  
  RESTART_PROFILE: 'hermes:action:restart_profile',
  STOP_PROFILE: 'hermes:action:stop_profile',
  START_PROFILE: 'hermes:action:start_profile',
  
  EXPORT_CONVERSATION: 'hermes:action:export_conversation',
  DELETE_CONVERSATION: 'hermes:action:delete_conversation',
  
  UPLOAD_DOCUMENT: 'hermes:action:upload_document',
  DELETE_DOCUMENT: 'hermes:action:delete_document',
  REBUILD_INDEX: 'hermes:action:rebuild_index',
} as const

export type HermesActionTypeKey = typeof HermesActionType[keyof typeof HermesActionType]

export interface HermesAuditLogListResponse {
  items: HermesAuditLog[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface HermesAuditActionTypeOption {
  value: string
  label: string
}

export const HermesActionTypeOptions: HermesAuditActionTypeOption[] = [
  { value: '', label: '全部操作' },
  { value: 'view', label: '查看类' },
  { value: 'action', label: '操作类' },
  { value: HermesActionType.VIEW_OVERVIEW, label: '查看系统概览' },
  { value: HermesActionType.VIEW_PROFILES, label: '查看Profile列表' },
  { value: HermesActionType.VIEW_PROFILE_DETAIL, label: '查看Profile详情' },
  { value: HermesActionType.VIEW_CONVERSATIONS, label: '查看对话列表' },
  { value: HermesActionType.VIEW_CONVERSATION_DETAIL, label: '查看对话详情' },
  { value: HermesActionType.VIEW_SKILLS, label: '查看技能列表' },
  { value: HermesActionType.VIEW_MCP, label: '查看MCP服务' },
  { value: HermesActionType.VIEW_TOOLS, label: '查看工具集' },
  { value: HermesActionType.VIEW_MEMORY, label: '查看记忆' },
  { value: HermesActionType.VIEW_CONFIG, label: '查看配置' },
  { value: HermesActionType.VIEW_KNOWLEDGE, label: '查看知识库' },
  { value: HermesActionType.RESTART_PROFILE, label: '重启Profile' },
  { value: HermesActionType.STOP_PROFILE, label: '停止Profile' },
  { value: HermesActionType.START_PROFILE, label: '启动Profile' },
  { value: HermesActionType.EXPORT_CONVERSATION, label: '导出对话' },
  { value: HermesActionType.DELETE_CONVERSATION, label: '删除对话' },
  { value: HermesActionType.UPLOAD_DOCUMENT, label: '上传文档' },
  { value: HermesActionType.DELETE_DOCUMENT, label: '删除文档' },
  { value: HermesActionType.REBUILD_INDEX, label: '重建索引' },
]

export type ProfileStatus = 'running' | 'starting' | 'stopped' | 'error'

export interface ProfileStats {
  total: number
  running: number
  stopped: number
  error: number
}

export interface ProfileSkillItem {
  name: string
  display_name: string
  path: string
}

export interface ProfileListItem {
  profile_name: string
  display_name: string
  status: ProfileStatus
  user_id: number | null
  user_name: string | null
  port: number | null
  api_url: string | null
  last_activity: string | null
  session_count: number
  created_at: string | null
}

export interface ProfileDetail {
  profile_name: string
  display_name: string
  status: ProfileStatus
  user_id: number | null
  user_name: string | null
  port: number | null
  api_url: string | null
  last_activity: string | null
  session_count: number
  created_at: string | null
  config_path: string | null
  is_default: boolean
  skills: ProfileSkillItem[]
  skill_count: number
  config_raw: string | null
}

export interface ProfileListResponse {
  items: ProfileListItem[]
  total: number
  running_count: number
  stopped_count: number
  error_count: number
}

export interface ProfileDetailResponse {
  profile: ProfileDetail
}

export interface ProfileActionResult {
  success: boolean
  message: string
  profile_name: string
  new_status: ProfileStatus | null
  error: string | null
}
