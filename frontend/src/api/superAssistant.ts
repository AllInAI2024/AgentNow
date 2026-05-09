import http from './http'
import type {
  APIResponse,
  SuperAssistantSession,
  SuperAssistantSessionListResponse,
  SuperAssistantChatStartResponse,
  SuperAssistantModelListResponse,
  SuperAssistantUploadResponse,
  SuperAssistantWorkspaceListResponse,
} from '@/types'

export const superAssistantApi = {
  listSessions: (): Promise<APIResponse<SuperAssistantSessionListResponse>> => {
    return http.get('/assistant/sessions')
  },

  getSession: (sessionId: string): Promise<APIResponse<SuperAssistantSession>> => {
    return http.get(`/assistant/session?session_id=${encodeURIComponent(sessionId)}`)
  },

  deleteSession: (sessionId: string): Promise<APIResponse<{ ok: boolean }>> => {
    return http.post('/assistant/session/delete', { session_id: sessionId })
  },

  listModels: (): Promise<APIResponse<SuperAssistantModelListResponse>> => {
    return http.get('/assistant/models')
  },

  listWorkspaces: (): Promise<APIResponse<SuperAssistantWorkspaceListResponse>> => {
    return http.get('/assistant/workspaces')
  },

  selectWorkspace: (path: string): Promise<APIResponse<SuperAssistantWorkspaceListResponse>> => {
    return http.post('/assistant/workspaces/select', { path })
  },

  upload: (sessionId: string | null | undefined, file: File): Promise<APIResponse<SuperAssistantUploadResponse>> => {
    const formData = new FormData()
    if (sessionId) formData.append('session_id', sessionId)
    formData.append('file', file)
    return http.post('/assistant/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  chatStart: (params: {
    session_id?: string
    message: string
    workspace?: string
    model?: string
    reasoning_effort?: string
    show_reasoning?: boolean
    attachments?: Array<Record<string, unknown>>
  }): Promise<APIResponse<SuperAssistantChatStartResponse>> => {
    return http.post('/assistant/chat/start', params)
  },

  chatCancel: (streamId: string): Promise<APIResponse<{ ok: boolean }>> => {
    const body = new URLSearchParams()
    body.append('stream_id', streamId)
    return http.post('/assistant/chat/cancel', body, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
}
