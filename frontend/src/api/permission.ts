import http from './http'
import type { APIResponse } from '@/types'

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

export interface PermissionCreate {
  parent_id: number
  name: string
  code: string
  type: number
  path: string | null
  icon: string | null
}

export interface PermissionUpdate {
  name?: string
  code?: string
  type?: number
  parent_id?: number
  path?: string | null
  icon?: string | null
}

export const permissionApi = {
  getList: (params?: { type?: number }): Promise<APIResponse<Permission[]>> => {
    return http.get('/permissions', { params }) as unknown as Promise<APIResponse<Permission[]>>
  },

  getTree: (): Promise<APIResponse<PermissionTree[]>> => {
    return http.get('/permissions/tree') as unknown as Promise<APIResponse<PermissionTree[]>>
  },

  getById: (id: number): Promise<APIResponse<Permission>> => {
    return http.get(`/permissions/${id}`) as unknown as Promise<APIResponse<Permission>>
  },

  create: (data: PermissionCreate): Promise<APIResponse<Permission>> => {
    return http.post('/permissions', data) as unknown as Promise<APIResponse<Permission>>
  },

  update: (id: number, data: PermissionUpdate): Promise<APIResponse<Permission>> => {
    return http.put(`/permissions/${id}`, data) as unknown as Promise<APIResponse<Permission>>
  },

  delete: (id: number): Promise<APIResponse<null>> => {
    return http.delete(`/permissions/${id}`) as unknown as Promise<APIResponse<null>>
  },
}

export const permissionTypeOptions = [
  { value: 1, label: '菜单' },
  { value: 2, label: '按钮' },
  { value: 3, label: 'API接口' },
]