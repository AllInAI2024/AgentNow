import http from './http'
import type { LoginParams, LoginResult, ChangePasswordParams, APIResponse, User } from '@/types'

export const authApi = {
  login: (params: LoginParams): Promise<LoginResult> => {
    return http.post('/auth/login', params)
  },

  changePassword: (params: ChangePasswordParams): Promise<APIResponse> => {
    return http.post('/auth/change-password', params)
  },

  getCurrentUser: (): Promise<User> => {
    return http.get('/auth/me')
  },

  logout: (): Promise<APIResponse> => {
    return http.post('/auth/logout')
  },
}
