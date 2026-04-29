export interface User {
  id: number
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
  created_at: string | null
  updated_at: string | null
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

export interface APIResponse<T = unknown> {
  code: number
  message: string
  data: T
}