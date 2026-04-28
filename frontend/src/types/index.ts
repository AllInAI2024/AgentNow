export interface User {
  id: number
  phone: string
  username: string
  role: 'admin' | 'user'
  is_active: boolean
  is_default_password: boolean
  hermes_profile: string | null
  created_at: string | null
  updated_at: string | null
}

export interface LoginParams {
  phone: string
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
