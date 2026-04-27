import http from './http'
import type { APIResponse } from '@/types'

export interface Permission {
  id: number
  parent_id: number
  enterprise_id: number | null
  name: string
  code: string
  type: number
  path: string | null
  component: string | null
  icon: string | null
  sort: number
  status: number
  visible: boolean
  keep_alive: boolean
  redirect: string | null
  permission_level: number
  description: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PermissionTree extends Permission {
  children: PermissionTree[]
}

export interface PermissionCreate {
  parent_id: number
  enterprise_id: number | null
  name: string
  code: string
  type: number
  path: string | null
  component: string | null
  icon: string | null
  sort: number
  visible: boolean
  keep_alive: boolean
  redirect: string | null
  permission_level: number
  description: string | null
}

export interface PermissionUpdate {
  name?: string
  code?: string
  type?: number
  parent_id?: number
  path?: string | null
  component?: string | null
  icon?: string | null
  sort?: number
  status?: number
  visible?: boolean
  keep_alive?: boolean
  redirect?: string | null
  permission_level?: number
  description?: string | null
}

export const permissionApi = {
  getList: (params?: { type?: number; status?: number }): Promise<APIResponse<Permission[]>> => {
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

export const permissionStatusOptions = [
  { value: 1, label: '启用' },
  { value: 0, label: '禁用' },
]

export const permissionLevelOptions = [
  { value: 1, label: '普通' },
  { value: 2, label: '敏感' },
  { value: 3, label: '高危' },
]
