import http from './http'
import type { User, CreateEmployeeParams, UpdateEmployeeParams, APIResponse } from '@/types'

export const employeeApi = {
  getList: (params?: { department_id?: number; is_active?: boolean }): Promise<APIResponse<User[]>> => {
    return http.get('/employees', { params })
  },

  getById: (id: number): Promise<APIResponse<User>> => {
    return http.get(`/employees/${id}`)
  },

  create: (params: CreateEmployeeParams): Promise<APIResponse<User>> => {
    return http.post('/employees', params)
  },

  update: (id: number, params: UpdateEmployeeParams): Promise<APIResponse<User>> => {
    return http.put(`/employees/${id}`, params)
  },

  delete: (id: number): Promise<APIResponse<null>> => {
    return http.delete(`/employees/${id}`)
  },

  resetPassword: (id: number): Promise<APIResponse<null>> => {
    return http.post(`/employees/${id}/reset-password`)
  },

  toggleStatus: (id: number): Promise<APIResponse<User>> => {
    return http.put(`/employees/${id}/status`)
  },
}
