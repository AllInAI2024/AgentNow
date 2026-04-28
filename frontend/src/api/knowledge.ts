import http from './http'
import type { 
  KnowledgeDoc, 
  KnowledgeDocList, 
  KnowledgeConfig,
  SyncStatus,
  DeleteResult,
  HermesFile,
  UpdateKnowledgeDocParams,
  APIResponse 
} from '@/types'

export const knowledgeApi = {
  getDocs: (params?: {
    page?: number
    page_size?: number
    keyword?: string
    category?: string
    status?: number
    sync_status?: number
  }): Promise<APIResponse<KnowledgeDocList>> => {
    return http.get('/knowledge/docs', { params })
  },

  getDocById: (id: number): Promise<APIResponse<KnowledgeDoc>> => {
    return http.get(`/knowledge/docs/${id}`)
  },

  uploadDoc: (
    formData: FormData,
    onUploadProgress?: (progressEvent: { loaded: number; total: number }) => void
  ): Promise<APIResponse<KnowledgeDoc>> => {
    return http.post('/knowledge/docs', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    })
  },

  updateDoc: (id: number, params: UpdateKnowledgeDocParams): Promise<APIResponse<KnowledgeDoc>> => {
    return http.put(`/knowledge/docs/${id}`, params)
  },

  deleteDoc: (id: number): Promise<APIResponse<DeleteResult>> => {
    return http.delete(`/knowledge/docs/${id}`)
  },

  downloadDoc: (id: number): Promise<Blob> => {
    return http.get(`/knowledge/docs/${id}/download`, {
      responseType: 'blob',
    })
  },

  syncDoc: (id: number): Promise<APIResponse<SyncStatus>> => {
    return http.post(`/knowledge/docs/${id}/sync`)
  },

  getCategories: (): Promise<APIResponse<string[]>> => {
    return http.get('/knowledge/categories')
  },

  getConfigs: (): Promise<APIResponse<KnowledgeConfig[]>> => {
    return http.get('/knowledge/configs')
  },

  updateConfig: (id: number, configValue: string): Promise<APIResponse<KnowledgeConfig>> => {
    return http.put(`/knowledge/configs/${id}`, {
      config_value: configValue,
    })
  },

  getHermesFiles: (): Promise<APIResponse<HermesFile[]>> => {
    return http.get('/knowledge/hermes-files')
  },
}
