import http from './http'
import type { LoginParams, LoginResult, ChangePasswordParams, APIResponse, User, PermissionTree, Role } from '@/types'

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

  getMenuPermissions: (): Promise<APIResponse<PermissionTree[]>> => {
    return http.get('/auth/menu-permissions') as unknown as Promise<APIResponse<PermissionTree[]>>
  },

  getUserRoles: (): Promise<APIResponse<Role[]>> => {
    return http.get('/auth/roles') as unknown as Promise<APIResponse<Role[]>>
  },

  getPermissions: (): Promise<APIResponse<string[]>> => {
    return http.get('/auth/permissions') as unknown as Promise<APIResponse<string[]>>
  },
}
