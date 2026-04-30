import http from './http'
import type { 
  APIResponse,
  UserAgent,
  UserAgentListResponse,
  AgentConversationListResponse,
  ChatResponseData,
  ConversationDetailResponse,
  EnableAgentResult,
} from '@/types'

export const agentApi = {
  getMyAgents: (): Promise<APIResponse<UserAgentListResponse>> => {
    return http.get('/agents/me')
  },

  enableAgent: (templateId?: number): Promise<APIResponse<EnableAgentResult>> => {
    const payload: Record<string, unknown> = {}
    if (templateId !== undefined) {
      payload.template_id = templateId
    }
    return http.post('/agents/me/enable', payload)
  },

  getAgentDetail: (agentId: number): Promise<APIResponse<UserAgent>> => {
    return http.get(`/agents/me/${agentId}`)
  },

  sendChat: (
    agentId: number,
    message: string,
    conversationId?: number,
    actionType: string = 'message',
    metadata?: Record<string, unknown>
  ): Promise<APIResponse<ChatResponseData>> => {
    const payload: Record<string, unknown> = {
      message,
      action_type: actionType,
    }
    if (conversationId !== undefined) {
      payload.conversation_id = conversationId
    }
    if (metadata) {
      payload.metadata = metadata
    }
    return http.post(`/agents/me/${agentId}/chat`, payload)
  },

  getConversations: (
    agentId: number,
    page: number = 1,
    pageSize: number = 20,
    status?: number
  ): Promise<APIResponse<AgentConversationListResponse>> => {
    const queryParams = new URLSearchParams()
    queryParams.append('page', String(page))
    queryParams.append('page_size', String(pageSize))
    if (status !== undefined) {
      queryParams.append('status', String(status))
    }
    const queryString = queryParams.toString()
    return http.get(`/agents/me/${agentId}/conversations${queryString ? `?${queryString}` : ''}`)
  },

  getConversationDetail: (
    agentId: number,
    conversationId: number
  ): Promise<APIResponse<ConversationDetailResponse>> => {
    return http.get(`/agents/me/${agentId}/conversations/${conversationId}`)
  },
}
