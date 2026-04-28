import http from './http'
import type { 
  HermesOverviewResponse,
  HermesHealthStatus,
  VersionCheckResponse,
  UpdateProgress,
  SkillListResponse,
  SkillDetailResponse,
  SkillInstallParams,
  SkillCreateParams,
  APIResponse 
} from '@/types'

export const hermesApi = {
  getOverview: (): Promise<APIResponse<HermesOverviewResponse>> => {
    return http.get('/hermes/overview')
  },

  getHealth: (): Promise<APIResponse<HermesHealthStatus>> => {
    return http.get('/hermes/health')
  },

  checkVersion: (): Promise<APIResponse<VersionCheckResponse>> => {
    return http.get('/hermes/version/check')
  },

  startUpdate: (): Promise<APIResponse<UpdateProgress>> => {
    return http.post('/hermes/version/update')
  },

  getUpdateProgress: (): Promise<APIResponse<UpdateProgress>> => {
    return http.get('/hermes/version/update/progress')
  },

  getSkills: (params?: { category?: string; search?: string }): Promise<APIResponse<SkillListResponse>> => {
    const queryParams = new URLSearchParams()
    if (params?.category) queryParams.append('category', params.category)
    if (params?.search) queryParams.append('search', params.search)
    const queryString = queryParams.toString()
    return http.get(`/hermes/skills${queryString ? `?${queryString}` : ''}`)
  },

  getSkillDetail: (skillName: string): Promise<APIResponse<SkillDetailResponse>> => {
    return http.get(`/hermes/skills/${encodeURIComponent(skillName)}`)
  },

  installSkill: (params: SkillInstallParams): Promise<APIResponse<Record<string, unknown>>> => {
    return http.post('/hermes/skills/install', params)
  },

  uninstallSkill: (skillName: string): Promise<APIResponse<Record<string, unknown>>> => {
    return http.post(`/hermes/skills/${encodeURIComponent(skillName)}/uninstall`)
  },

  createSkill: (params: SkillCreateParams): Promise<APIResponse<Record<string, unknown>>> => {
    return http.post('/hermes/skills/create', params)
  },

  updateSkill: (skillName: string): Promise<APIResponse<Record<string, unknown>>> => {
    return http.post(`/hermes/skills/${encodeURIComponent(skillName)}/update`)
  },

  browseAvailableSkills: (): Promise<APIResponse<unknown[]>> => {
    return http.get('/hermes/skills/available/browse')
  },

  uploadSkill: (file: File, category?: string): Promise<APIResponse<Record<string, unknown>>> => {
    const formData = new FormData()
    formData.append('file', file)
    if (category) {
      formData.append('category', category)
    }
    return http.post('/hermes/skills/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
