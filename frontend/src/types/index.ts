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
