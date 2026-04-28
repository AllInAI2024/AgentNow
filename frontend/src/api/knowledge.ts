import http from './http'
import type { 
  KnowledgeDoc, 
  KnowledgeDocDetail,
  KnowledgeDocList, 
  KnowledgeConfig,
  DeleteResult,
  AllTagsResponse,
  AllCategoriesResponse,
  FileSystemInfo,
  StatisticsResponse,
  UpdateKnowledgeDocParams,
  UpdateKnowledgeDocContentParams,
  APIResponse 
} from '@/types'

export const knowledgeApi = {
  getDocs: (params?: {
    page?: number
    page_size?: number
    keyword?: string
    category?: string
    tag?: string
    is_public?: boolean
    created_by?: number
    sort_by?: string
    sort_order?: string
  }): Promise<APIResponse<KnowledgeDocList>> => {
    return http.get('/knowledge/docs', { params })
  },

  getDocById: (
    id: number,
    includeContent: boolean = false
  ): Promise<APIResponse<KnowledgeDocDetail>> => {
    return http.get(`/knowledge/docs/${id}`, {
      params: { include_content: includeContent }
    })
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

  createMarkdownDoc: (
    params: {
      title: string
      description?: string
      tags?: string
      category?: string
      is_public?: boolean
      content?: string
      filename?: string
    }
  ): Promise<APIResponse<KnowledgeDoc>> => {
    const formData = new FormData()
    formData.append('title', params.title)
    if (params.description) formData.append('description', params.description)
    if (params.tags) formData.append('tags', params.tags)
    if (params.category) formData.append('category', params.category)
    formData.append('is_public', String(params.is_public ?? true))
    formData.append('content', params.content ?? '')
    if (params.filename) formData.append('filename', params.filename)

    return http.post('/knowledge/docs/markdown', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  updateDoc: (
    id: number,
    params: UpdateKnowledgeDocParams
  ): Promise<APIResponse<KnowledgeDoc>> => {
    return http.put(`/knowledge/docs/${id}`, params)
  },

  updateDocContent: (
    id: number,
    params: UpdateKnowledgeDocContentParams
  ): Promise<APIResponse<KnowledgeDoc>> => {
    return http.put(`/knowledge/docs/${id}/content`, params)
  },

  deleteDoc: (
    id: number,
    hardDelete: boolean = false
  ): Promise<APIResponse<DeleteResult>> => {
    return http.delete(`/knowledge/docs/${id}`, {
      params: { hard_delete: hardDelete }
    })
  },

  downloadDoc: (id: number): Promise<Blob> => {
    return http.get(`/knowledge/docs/${id}/download`, {
      responseType: 'blob',
    })
  },

  getCategories: (): Promise<APIResponse<AllCategoriesResponse>> => {
    return http.get('/knowledge/categories')
  },

  getTags: (): Promise<APIResponse<AllTagsResponse>> => {
    return http.get('/knowledge/tags')
  },

  getStatistics: (): Promise<APIResponse<StatisticsResponse>> => {
    return http.get('/knowledge/statistics')
  },

  getStorageInfo: (): Promise<APIResponse<FileSystemInfo>> => {
    return http.get('/knowledge/storage')
  },

  getConfigs: (): Promise<APIResponse<KnowledgeConfig[]>> => {
    return http.get('/knowledge/configs')
  },

  updateConfig: (
    id: number,
    configValue: string
  ): Promise<APIResponse<KnowledgeConfig>> => {
    return http.put(`/knowledge/configs/${id}`, {
      config_value: configValue,
    })
  },
}
