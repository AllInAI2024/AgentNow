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
  MCPServiceListResponse,
  MCPServiceDetailResponse,
  MCPServiceTestResult,
  BuiltinToolListResponse,
  MemoryResponse,
  ProfileMemoryListResponse,
  ConfigResponse,
  ConfigProfileListResponse,
  HermesKnowledgeStatus,
  HermesKnowledgeListResponse,
  HermesKnowledgeDocDetail,
  FileTypeStat,
  HermesAuditLogListResponse,
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

  getMcpServices: (): Promise<APIResponse<MCPServiceListResponse>> => {
    return http.get('/hermes/mcp')
  },

  getMcpServiceDetail: (serviceName: string): Promise<APIResponse<MCPServiceDetailResponse>> => {
    return http.get(`/hermes/mcp/${encodeURIComponent(serviceName)}`)
  },

  testMcpService: (serviceName: string): Promise<APIResponse<MCPServiceTestResult>> => {
    return http.post(`/hermes/mcp/${encodeURIComponent(serviceName)}/test`)
  },

  getTools: (params?: { category?: string; search?: string }): Promise<APIResponse<BuiltinToolListResponse>> => {
    const queryParams = new URLSearchParams()
    if (params?.category) queryParams.append('category', params.category)
    if (params?.search) queryParams.append('search', params.search)
    const queryString = queryParams.toString()
    return http.get(`/hermes/tools${queryString ? `?${queryString}` : ''}`)
  },

  getMemoryList: (): Promise<APIResponse<ProfileMemoryListResponse>> => {
    return http.get('/hermes/memory/list')
  },

  getProfileMemory: (profileName: string): Promise<APIResponse<MemoryResponse>> => {
    return http.get(`/hermes/profiles/${encodeURIComponent(profileName)}/memory`)
  },

  getConfigProfiles: (): Promise<APIResponse<ConfigProfileListResponse>> => {
    return http.get('/hermes/config/profiles')
  },

  getGlobalConfig: (): Promise<APIResponse<ConfigResponse>> => {
    return http.get('/hermes/config')
  },

  getProfileConfig: (profileName: string): Promise<APIResponse<ConfigResponse>> => {
    return http.get(`/hermes/config/${encodeURIComponent(profileName)}`)
  },

  getKnowledgeStatus: (): Promise<APIResponse<HermesKnowledgeStatus>> => {
    return http.get('/hermes/knowledge/status')
  },

  getKnowledgeDocs: (params?: {
    page?: number
    page_size?: number
    keyword?: string
    file_type?: string
    category?: string
  }): Promise<APIResponse<HermesKnowledgeListResponse>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.page_size) queryParams.append('page_size', String(params.page_size))
    if (params?.keyword) queryParams.append('keyword', params.keyword)
    if (params?.file_type) queryParams.append('file_type', params.file_type)
    if (params?.category) queryParams.append('category', params.category)
    const queryString = queryParams.toString()
    return http.get(`/hermes/knowledge/documents${queryString ? `?${queryString}` : ''}`)
  },

  getKnowledgeDocDetail: (docId: string): Promise<APIResponse<HermesKnowledgeDocDetail>> => {
    return http.get(`/hermes/knowledge/documents/${encodeURIComponent(docId)}`)
  },

  getKnowledgeFileTypes: (): Promise<APIResponse<FileTypeStat[]>> => {
    return http.get('/hermes/knowledge/file-types')
  },

  getAuditLogs: (params?: {
    page?: number
    page_size?: number
    action?: string
    user_id?: number
    user_name?: string
    target_type?: string
    start_time?: string
    end_time?: string
  }): Promise<APIResponse<HermesAuditLogListResponse>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.page_size) queryParams.append('page_size', String(params.page_size))
    if (params?.action) queryParams.append('action', params.action)
    if (params?.user_id) queryParams.append('user_id', String(params.user_id))
    if (params?.user_name) queryParams.append('user_name', params.user_name)
    if (params?.target_type) queryParams.append('target_type', params.target_type)
    if (params?.start_time) queryParams.append('start_time', params.start_time)
    if (params?.end_time) queryParams.append('end_time', params.end_time)
    const queryString = queryParams.toString()
    return http.get(`/hermes/audit${queryString ? `?${queryString}` : ''}`)
  },
}
