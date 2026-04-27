import http from './http'
import type { Department, DepartmentTree, CreateDepartmentParams, UpdateDepartmentParams, APIResponse } from '@/types'

export const departmentApi = {
  getList: (params?: { status?: number }): Promise<APIResponse<Department[]>> => {
    return http.get('/departments', { params })
  },

  getTree: (): Promise<APIResponse<DepartmentTree[]>> => {
    return http.get('/departments/tree')
  },

  getById: (id: number): Promise<APIResponse<Department>> => {
    return http.get(`/departments/${id}`)
  },

  create: (params: CreateDepartmentParams): Promise<APIResponse<Department>> => {
    return http.post('/departments', params)
  },

  update: (id: number, params: UpdateDepartmentParams): Promise<APIResponse<Department>> => {
    return http.put(`/departments/${id}`, params)
  },

  delete: (id: number): Promise<APIResponse<null>> => {
    return http.delete(`/departments/${id}`)
  },
}
