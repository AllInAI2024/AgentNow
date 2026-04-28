import http from './http'
import type { 
  HermesOverviewResponse,
  HermesHealthStatus,
  VersionCheckResponse,
  UpdateProgress,
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
}
