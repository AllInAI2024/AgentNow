import http from './http'
import type { APIResponse } from '@/types'

export interface Role {
  id: number
  name: string
  code: string
  description: string | null
  created_at: string | null
  updated_at: string | null
}

export interface RoleWithPermissions extends Role {
  permissions: number[]
}

export interface RoleCreate {
  name: string
  code: string
  description?: string
}

export interface RoleUpdate {
  name?: string
  description?: string
}

export interface AssignPermissionsRequest {
  permission_ids: number[]
}

export interface AssignRolesRequest {
  role_ids: number[]
}

export const roleApi = {
  getList: (): Promise<APIResponse<Role[]>> => {
    return http.get('/roles') as unknown as Promise<APIResponse<Role[]>>
  },

  getById: (id: number): Promise<APIResponse<RoleWithPermissions>> => {
    return http.get(`/roles/${id}`) as unknown as Promise<APIResponse<RoleWithPermissions>>
  },

  create: (data: RoleCreate): Promise<APIResponse<Role>> => {
    return http.post('/roles', data) as unknown as Promise<APIResponse<Role>>
  },

  update: (id: number, data: RoleUpdate): Promise<APIResponse<Role>> => {
    return http.put(`/roles/${id}`, data) as unknown as Promise<APIResponse<Role>>
  },

  delete: (id: number): Promise<APIResponse<null>> => {
    return http.delete(`/roles/${id}`) as unknown as Promise<APIResponse<null>>
  },

  getPermissions: (roleId: number): Promise<APIResponse<number[]>> => {
    return http.get(`/roles/${roleId}/permissions`) as unknown as Promise<APIResponse<number[]>>
  },

  assignPermissions: (roleId: number, permissionIds: number[]): Promise<APIResponse<number[]>> => {
    return http.put(`/roles/${roleId}/permissions`, { permission_ids: permissionIds }) as unknown as Promise<APIResponse<number[]>>
  },

  getUserRoles: (userId: number): Promise<APIResponse<number[]>> => {
    return http.get(`/roles/users/${userId}`) as unknown as Promise<APIResponse<number[]>>
  },

  assignUserRoles: (userId: number, roleIds: number[]): Promise<APIResponse<number[]>> => {
    return http.put(`/roles/users/${userId}`, { role_ids: roleIds }) as unknown as Promise<APIResponse<number[]>>
  },
}
