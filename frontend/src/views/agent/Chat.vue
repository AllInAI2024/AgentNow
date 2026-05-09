<template>
  <MainLayout>
    <div class="chat-page">
      <div class="chat-container">
        <div class="chat-sidebar">
          <div class="sidebar-header">
            <div class="header-left" @click="handleGoBack">
              <LeftOutlined class="back-icon" />
              <span class="sidebar-title">{{ currentAgent?.display_name || '智能体' }}</span>
            </div>
            <a-button type="text" class="new-chat-btn" @click="handleNewChat">
              <PlusOutlined />
            </a-button>
          </div>
          
          <div class="sidebar-content">
            <a-spin :spinning="loadingConversations">
              <div class="conversation-list" v-if="conversations.length > 0">
                <div
                  v-for="conv in conversations"
                  :key="conv.id"
                  class="conversation-item"
                  :class="{ 'conversation-item-active': currentConversationId === conv.id }"
                  @click="handleSelectConversation(conv)"
                >
                  <div class="conversation-icon">
                    <MessageOutlined />
                  </div>
                  <div class="conversation-info">
                    <div class="conversation-title">{{ conv.title || '新对话' }}</div>
                    <div class="conversation-meta">
                      <span class="conversation-time">{{ formatTime(conv.last_message_at || conv.started_at) }}</span>
                      <span class="conversation-stage" :class="getStageClass(conv.current_stage)">
                        {{ getStageLabel(conv.current_stage) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <a-empty 
                v-else-if="!loadingConversations" 
                description="暂无对话，开始新对话吧"
                class="empty-conversations"
              >
                <template #image>
                  <MessageOutlined class="empty-icon" />
                </template>
              </a-empty>
            </a-spin>
          </div>
        </div>

        <div class="chat-main">
          <div class="chat-header" v-if="currentConversation">
            <div class="chat-agent-info">
              <div class="chat-agent-icon">
                <RobotOutlined />
              </div>
              <div class="chat-agent-detail">
                <div class="chat-agent-name">{{ currentAgent?.display_name || '智能体' }}</div>
                <div class="chat-agent-status">
                  <span class="status-dot"></span>
                  <span class="current-stage-badge" :class="getStageClass(currentConversation.current_stage)">
                    {{ getStageLabel(currentConversation.current_stage) }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="chat-status-bar" v-if="currentConversation">
              <div class="status-item" :class="{ confirmed: currentConversation.outline_confirmed }">
                <CheckCircleOutlined v-if="currentConversation.outline_confirmed" class="status-icon confirmed" />
                <ClockCircleOutlined v-else class="status-icon pending" />
                <span class="status-text">大纲确认</span>
              </div>
              <div class="status-divider"></div>
              <div class="status-item" :class="{ confirmed: currentConversation.template_confirmed }">
                <CheckCircleOutlined v-if="currentConversation.template_confirmed" class="status-icon confirmed" />
                <ClockCircleOutlined v-else class="status-icon pending" />
                <span class="status-text">模板确认</span>
              </div>
              <div class="status-divider"></div>
              <div class="status-item" :class="{ confirmed: currentConversation.final_generation_confirmed }">
                <CheckCircleOutlined v-if="currentConversation.final_generation_confirmed" class="status-icon confirmed" />
                <ClockCircleOutlined v-else class="status-icon pending" />
                <span class="status-text">生成完成</span>
              </div>
            </div>
          </div>

          <div v-if="debugEnabled" style="position: fixed; right: 16px; bottom: 90px; width: 380px; max-height: 45vh; overflow: auto; z-index: 9999; background: rgba(0,0,0,0.75); color: #fff; padding: 12px; border-radius: 12px; font-size: 12px;">
            <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom: 8px;">
              <div>AGENT_DEBUG</div>
              <a-button size="small" type="primary" @click.prevent.stop="clearDebug">清空</a-button>
            </div>
            <div v-for="(evt, idx) in debugEvents.slice(-60)" :key="idx" style="margin-bottom: 6px; word-break: break-all;">
              <div style="opacity:0.85;">{{ evt.ts }} · {{ evt.type }}</div>
              <div v-if="evt.data !== undefined" style="opacity:0.95;">{{ typeof evt.data === 'string' ? evt.data : JSON.stringify(evt.data) }}</div>
            </div>
          </div>

          <div class="chat-messages" ref="messagesContainer">
            <a-spin :spinning="loadingMessages">
              <template v-if="messages.length > 0">
                <div
                  v-for="(msg, index) in messages"
                  :key="index"
                  class="message-wrapper"
                  :class="{ 'message-user': msg.role === 'user', 'message-assistant': msg.role === 'assistant' }"
                >
                  <div class="message-avatar">
                    <template v-if="msg.role === 'user'">
                      <a-avatar class="user-avatar" :size="36">
                        {{ userStore.userInfo?.username?.charAt(0) || 'U' }}
                      </a-avatar>
                    </template>
                    <template v-else>
                      <div class="agent-avatar">
                        <RobotOutlined />
                      </div>
                    </template>
                  </div>
                  <div class="message-content">
                    <div class="message-sender">
                      {{ msg.role === 'user' ? (userStore.userInfo?.username || '我') : (currentAgent?.display_name || '智能体') }}
                    </div>
                    <div class="message-bubble">
                      <div 
                        class="message-text" 
                        :class="{ 'markdown-content': msg.role === 'assistant' }"
                        v-html="renderMarkdown(msg.content)"
                      ></div>
                    </div>
                    <div class="message-time" v-if="msg.timestamp">
                      {{ formatMessageTime(msg.timestamp) }}
                    </div>
                  </div>
                </div>
              </template>

              <div v-else class="welcome-section" v-if="!loadingMessages">
                <div class="welcome-icon-wrapper">
                  <RobotOutlined class="welcome-icon" />
                </div>
                <h2 class="welcome-title">你好，我是{{ currentAgent?.display_name || '智能体助手' }}</h2>
                <p class="welcome-desc">
                  {{ currentAgent?.template?.description || '我可以帮您完成各种任务，有什么需要帮助的吗？' }}
                </p>
                <div class="quick-actions" v-if="quickActions.length > 0">
                  <div
                    v-for="(action, index) in quickActions"
                    :key="index"
                    class="quick-action-card"
                    @click="handleQuickAction(action)"
                  >
                    <div class="quick-action-icon">
                      <component :is="getQuickActionIcon(action.icon)" />
                    </div>
                    <div class="quick-action-text">{{ action.text }}</div>
                  </div>
                </div>
              </div>

              <div v-if="isTyping" class="message-wrapper message-assistant">
                <div class="message-avatar">
                  <div class="agent-avatar">
                    <RobotOutlined />
                  </div>
                </div>
                <div class="message-content">
                  <div class="message-bubble typing-bubble">
                    <div class="typing-indicator">
                      <span class="typing-dot"></span>
                      <span class="typing-dot"></span>
                      <span class="typing-dot"></span>
                    </div>
                  </div>
                </div>
              </div>
            </a-spin>
          </div>

          <div class="generated-files-section" v-if="generatedFiles.length > 0">
            <div class="files-header">
              <FileTextOutlined class="files-icon" />
              <span class="files-title">生成的文件</span>
              <span class="files-count">{{ generatedFiles.length }} 个版本</span>
            </div>
            <div class="files-list">
              <div 
                v-for="file in sortedGeneratedFiles" 
                :key="file.id"
                class="file-item"
                :class="{ 'file-item-failed': file.generation_status === 2 }"
              >
                <div class="file-info">
                  <FileTextOutlined 
                    class="file-type-icon" 
                    :class="{ 'file-type-icon-failed': file.generation_status === 2 }"
                  />
                  <div class="file-details">
                    <div class="file-name">
                      {{ file.file_name }}
                      <span v-if="file.template_name" class="file-template">
                        ({{ file.template_name }})
                      </span>
                    </div>
                    <div class="file-meta">
                      <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                      <span class="file-status" :class="getGenerationStatusClass(file.generation_status)">
                        {{ getGenerationStatusLabel(file.generation_status) }}
                      </span>
                      <span class="file-version">v{{ file.version_no }}</span>
                      <span v-if="file.created_at" class="file-time">
                        {{ formatFileTime(file.created_at) }}
                      </span>
                    </div>
                    <div v-if="file.generation_status === 2 && file.error_message" class="file-error">
                      <a-alert
                        message="失败原因"
                        :description="file.error_message"
                        type="error"
                        show-icon
                        :closable="false"
                        class="error-alert"
                      />
                    </div>
                  </div>
                </div>
                <div class="file-actions">
                  <a-button 
                    type="primary"
                    size="small"
                    class="download-btn"
                    :disabled="file.generation_status !== 1"
                    @click="handleDownloadFile(file)"
                  >
                    <DownloadOutlined /> 下载
                  </a-button>
                  <a-button 
                    v-if="file.generation_status === 2"
                    type="primary"
                    size="small"
                    class="retry-btn"
                    danger
                    @click="handleRetryGenerate(file)"
                  >
                    <SyncOutlined /> 重试
                  </a-button>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-action-bar" v-if="showActionButtons">
            <div class="action-buttons">
              <a-button 
                type="primary" 
                size="large"
                class="action-btn confirm-btn"
                v-if="canConfirmOutline"
                html-type="button"
                @click.prevent.stop="handleConfirmOutline"
              >
                <CheckOutlined /> 确认大纲
              </a-button>
              <a-button 
                size="large"
                class="action-btn revise-btn"
                v-if="canReviseOutline"
                html-type="button"
                @click.prevent.stop="handleReviseOutline"
              >
                <EditOutlined /> 调整大纲
              </a-button>
              <a-button 
                type="primary" 
                size="large"
                class="action-btn confirm-btn"
                v-if="canConfirmTemplate"
                html-type="button"
                @click.prevent.stop="handleConfirmTemplate"
              >
                <CheckOutlined /> 确认模板
              </a-button>
              <a-button 
                type="primary" 
                size="large"
                class="action-btn generate-btn"
                v-if="canGeneratePPT"
                html-type="button"
                @click.prevent.stop="handleGeneratePPT"
              >
                <FileTextOutlined /> 生成 PPT
              </a-button>
            </div>
          </div>

          <div class="chat-input-area">
            <div class="input-wrapper">
              <a-textarea
                v-model:value="inputMessage"
                placeholder="输入您的问题或需求..."
                :rows="4"
                :auto-size="{ minRows: 4, maxRows: 8 }"
                class="chat-input"
                @keydown="handleKeyDown"
                :disabled="!currentAgent || isTyping"
              />
              <div class="input-actions">
                <a-button
                  type="primary"
                  shape="circle"
                html-type="button"
                  :disabled="!inputMessage.trim() || isTyping || !currentAgent"
                  :loading="isTyping"
                @click.prevent.stop="handleSendMessage"
                >
                  <SendOutlined />
                </a-button>
              </div>
            </div>
            <div class="input-tip">
              按 Enter 发送，Shift+Enter 换行
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import {
  RobotOutlined,
  MessageOutlined,
  LeftOutlined,
  PlusOutlined,
  SendOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  QuestionCircleOutlined,
  BulbOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CheckOutlined,
  EditOutlined,
  DownloadOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue'
import { agentApi } from '@/api/agent'
import type { 
  UserAgent, 
  AgentConversation, 
  ChatMessage,
  AgentGeneratedFile,
  StructuredResult,
} from '@/types'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const agentId = computed(() => Number(route.params.agentId))
const currentAgent = ref<UserAgent | null>(null)
const currentConversationId = ref<number | null>(null)
const currentConversation = ref<AgentConversation | null>(null)
const conversations = ref<AgentConversation[]>([])
const messages = ref<ChatMessage[]>([])
const generatedFiles = ref<AgentGeneratedFile[]>([])
const structuredResult = ref<StructuredResult | null>(null)
const inputMessage = ref('')
const loadingConversations = ref(false)
const loadingMessages = ref(false)
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const debugEnabled = ref(false)
const debugEvents = ref<Array<{ ts: string; type: string; data?: unknown }>>([])
const pushDebug = (type: string, data?: unknown) => {
  if (!debugEnabled.value) return
  const evt = { ts: new Date().toISOString(), type, data }
  debugEvents.value.push(evt)
  if (debugEvents.value.length > 120) {
    debugEvents.value = debugEvents.value.slice(-120)
  }
  try {
    sessionStorage.setItem('AGENT_DEBUG_EVENTS', JSON.stringify(debugEvents.value))
  } catch {}
  try {
    ;(window as any).__agentDebugEvents = debugEvents.value
  } catch {}
  console.info('[AGENT_DEBUG]', type, data)
}

const initDebug = () => {
  debugEnabled.value = localStorage.getItem('AGENT_DEBUG') === '1'
  if (!debugEnabled.value) return
  try {
    const raw = sessionStorage.getItem('AGENT_DEBUG_EVENTS')
    if (raw) debugEvents.value = JSON.parse(raw)
  } catch {}

  pushDebug('debug_enabled')

  window.addEventListener('beforeunload', () => {
    try {
      sessionStorage.setItem(
        'AGENT_DEBUG_LAST_BEFOREUNLOAD',
        JSON.stringify({ ts: new Date().toISOString(), href: window.location.href })
      )
    } catch {}
  })
  window.addEventListener('pagehide', (e) => {
    pushDebug('pagehide', { persisted: (e as PageTransitionEvent).persisted })
  })
  window.addEventListener('visibilitychange', () => {
    pushDebug('visibilitychange', { state: document.visibilityState })
  })
  window.addEventListener('error', (e) => {
    pushDebug('window_error', {
      message: (e as ErrorEvent).message,
      filename: (e as ErrorEvent).filename,
      lineno: (e as ErrorEvent).lineno,
      colno: (e as ErrorEvent).colno,
    })
  })
  window.addEventListener('unhandledrejection', (e) => {
    pushDebug('unhandledrejection', { reason: (e as PromiseRejectionEvent).reason })
  })

  try {
    const last = sessionStorage.getItem('AGENT_DEBUG_LAST_BEFOREUNLOAD')
    if (last) pushDebug('last_beforeunload', JSON.parse(last))
  } catch {}
}

const clearDebug = () => {
  if (!debugEnabled.value) return
  debugEvents.value = []
  try {
    sessionStorage.removeItem('AGENT_DEBUG_EVENTS')
  } catch {}
  pushDebug('debug_cleared')
}

marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderMarkdown = (content: string | null | undefined): string => {
  if (!content) return ''
  try {
    return marked.parse(content) as string
  } catch (e) {
    console.error('Markdown parse error:', e)
    return content || ''
  }
}

const quickActions = computed(() => [
  { text: '帮我写一个公司介绍的 10 页 PPT', icon: 'file' },
  { text: '帮我做一份产品宣讲 PPT', icon: 'bulb' },
  { text: '我需要一份客户拜访汇报', icon: 'thunderbolt' },
])

const showActionButtons = computed(() => {
  return !!currentConversationId.value
})

const canConfirmOutline = computed(() => {
  return currentConversation.value?.current_stage === 'content_draft'
})

const canReviseOutline = computed(() => {
  return currentConversation.value?.current_stage === 'content_draft'
})

const canConfirmTemplate = computed(() => {
  return currentConversation.value?.current_stage === 'template_select'
})

const canGeneratePPT = computed(() => {
  return !!currentConversationId.value
})

const getQuickActionIcon = (icon: string) => {
  const iconMap: Record<string, unknown> = {
    'file': FileTextOutlined,
    'bulb': BulbOutlined,
    'question': QuestionCircleOutlined,
    'thunderbolt': ThunderboltOutlined,
  }
  return iconMap[icon] || MessageOutlined
}

const getStageLabel = (stage: string | null | undefined): string => {
  const stageMap: Record<string, string> = {
    'welcome': '欢迎',
    'clarifying': '需求确认',
    'collecting_requirements': '确认需求',
    'template_select': '确认模板',
    'content_draft': '内容草稿',
    'ready_generate': '待生成',
    'final_generating': '生成中',
    'content_ready': '内容已就绪',
    'completed': '已完成',
    'chatting': '对话中',
  }
  return stageMap[stage || 'chatting'] || '对话中'
}

const getStageClass = (stage: string | null | undefined): string => {
  const classMap: Record<string, string> = {
    'welcome': 'stage-welcome',
    'clarifying': 'stage-clarifying',
    'collecting_requirements': 'stage-clarifying',
    'template_select': 'stage-template',
    'content_draft': 'stage-outline',
    'ready_generate': 'stage-confirmed',
    'final_generating': 'stage-generating',
    'completed': 'stage-completed',
  }
  return classMap[stage || ''] || ''
}

const loadAgentDetail = async () => {
  if (!agentId.value) return
  try {
    const response = await agentApi.getAgentDetail(agentId.value)
    if (response.code === 200 && response.data) {
      currentAgent.value = response.data as UserAgent
    }
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    message.error('获取智能体信息失败')
  }
}

const loadConversations = async () => {
  if (!agentId.value) return
  loadingConversations.value = true
  try {
    const response = await agentApi.getConversations(agentId.value, 1, 50)
    if (response.code === 200 && response.data) {
      conversations.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
  } finally {
    loadingConversations.value = false
  }
}

const loadConversationDetail = async (conversationId: number) => {
  if (!agentId.value) return
  loadingMessages.value = true
  pushDebug('detail_load_start', { conversationId })
  try {
    const response = await agentApi.getConversationDetail(agentId.value, conversationId)
    if (response.code === 200 && response.data) {
      currentConversation.value = response.data.conversation
      const serverMessages = response.data.messages || []
      if (serverMessages.length > 0 || messages.value.length === 0) {
        messages.value = serverMessages
      }
      generatedFiles.value = (response.data.files || []) as AgentGeneratedFile[]
      structuredResult.value = response.data.structured_result || null
      pushDebug('detail_load_ok', {
        conversationId,
        serverMessagesLen: serverMessages.length,
        clientMessagesLen: messages.value.length,
        filesLen: (response.data.files || []).length,
        hasStructured: !!response.data.structured_result,
        stage: response.data.conversation?.current_stage,
      })
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('获取会话详情失败:', error)
    message.error('加载对话失败')
    const err = error as any
    pushDebug('detail_load_error', {
      conversationId,
      status: err?.response?.status,
      detail: err?.response?.data?.detail || err?.response?.data?.message,
    })
  } finally {
    loadingMessages.value = false
  }
}

const handleGoBack = () => {
  router.push({ name: 'MyAgents' })
}

const handleNewChat = () => {
  currentConversationId.value = null
  currentConversation.value = null
  messages.value = []
  structuredResult.value = null
  inputMessage.value = ''
}

const handleSelectConversation = (conv: AgentConversation) => {
  currentConversationId.value = conv.id
  loadConversationDetail(conv.id)
}

const handleQuickAction = async (action: { text: string; icon: string }) => {
  await sendMessageWithAction(action.text, 'message')
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessageWithAction = async (
  msg: string,
  actionType: string = 'message',
  restoreInputOnError: boolean = false
) => {
  if (!currentAgent.value || isTyping.value) return
  pushDebug('send_start', {
    actionType,
    agentId: agentId.value,
    conversationId: currentConversationId.value,
    msgLen: msg?.length || 0,
  })

  const shouldAppendUserMessage = actionType === 'message'

  if (shouldAppendUserMessage && msg && msg.trim()) {
    const userMessage: ChatMessage = {
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMessage)
  }
  
  inputMessage.value = ''
  isTyping.value = true
  
  await nextTick()
  scrollToBottom()

  try {
    const response = await agentApi.sendChat(
      agentId.value,
      msg,
      currentConversationId.value || undefined,
      actionType
    )
    pushDebug('send_response', { code: (response as any)?.code })

    if (response.code === 200 && response.data) {
      const data = response.data
      
      if (data.conversation) {
        if (!currentConversationId.value) {
          currentConversationId.value = data.conversation.id
          currentConversation.value = data.conversation
          await loadConversations()
        } else {
          currentConversation.value = data.conversation
        }
      }

      if (data.assistant_message) {
        messages.value.push({
          role: 'assistant',
          content: data.assistant_message.content,
          timestamp: new Date().toISOString(),
        })
      }

      if (currentConversationId.value) {
        await loadConversationDetail(currentConversationId.value)
        await loadConversations()
      }

      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    const err = error as any
    const detail = err?.response?.data?.detail || err?.response?.data?.message
    pushDebug('send_error', {
      detail,
      status: err?.response?.status,
      url: err?.config?.url,
    })
    message.error(detail || '发送消息失败，请稍后重试')
    if (shouldAppendUserMessage && msg && msg.trim()) {
      messages.value.push({
        role: 'assistant',
        content: detail || '发送失败，请稍后重试',
        timestamp: new Date().toISOString(),
      })
    }
    if (restoreInputOnError) {
      inputMessage.value = msg
    }
  } finally {
    isTyping.value = false
  }
}

const handleSendMessage = async () => {
  if (!currentAgent.value || isTyping.value) return
  const msg = inputMessage.value.trim()
  if (!msg) return
  pushDebug('send_click', { conversationId: currentConversationId.value, msgLen: msg.length })
  inputMessage.value = ''
  await sendMessageWithAction(msg, 'message', true)
}

const handleConfirmOutline = async () => {
  await sendMessageWithAction('确认大纲，继续往下做', 'confirm_outline')
}

const handleReviseOutline = async () => {
  inputMessage.value = '我想调整一下大纲'
}

const handleConfirmTemplate = async () => {
  await sendMessageWithAction('使用公司标准模板', 'confirm_template')
}

const handleGeneratePPT = async () => {
  if (!currentConversationId.value) {
    message.warning('请先完成当前对话')
    return
  }

  if (isTyping.value) return

  isTyping.value = true
  try {
    const response = await agentApi.generatePPT(agentId.value, currentConversationId.value)
    if (response.code === 200) {
      message.success('PPT 生成成功')
      await loadConversationDetail(currentConversationId.value)
      await loadConversations()
    }
  } catch (error) {
    console.error('生成 PPT 失败:', error)
    const err = error as any
    const detail = err?.response?.data?.detail || err?.response?.data?.message
    message.error(detail || '生成 PPT 失败，请稍后重试')
  } finally {
    isTyping.value = false
  }
}

const sortedGeneratedFiles = computed(() => {
  return [...generatedFiles.value].sort((a, b) => {
    if (b.version_no !== a.version_no) {
      return b.version_no - a.version_no
    }
    if (b.created_at && a.created_at) {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    }
    return b.id - a.id
  })
})

const formatFileTime = (timeStr: string): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hour = date.getHours().toString().padStart(2, '0')
  const minute = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

const handleRetryGenerate = async (_file: AgentGeneratedFile) => {
  if (!currentConversationId.value) {
    message.warning('请先完成当前对话')
    return
  }

  if (isTyping.value) return

  isTyping.value = true
  try {
    const response = await agentApi.generatePPT(agentId.value, currentConversationId.value, undefined, true)
    if (response.code === 200) {
      message.success('重试成功')
      await loadConversationDetail(currentConversationId.value)
      await loadConversations()
    }
  } catch (error) {
    console.error('重试生成 PPT 失败:', error)
    const err = error as any
    const detail = err?.response?.data?.detail || err?.response?.data?.message
    message.error(detail || '重试失败，请稍后重试')
  } finally {
    isTyping.value = false
  }
}

const handleDownloadFile = async (file: AgentGeneratedFile) => {
  if (file.generation_status !== 1) {
    message.warning('文件生成未完成或已失败')
    return
  }
  
  try {
    const blob = await agentApi.downloadFile(agentId.value, file.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.file_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('下载已开始')
  } catch (error) {
    console.error('下载文件失败:', error)
    message.error('下载文件失败')
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

const getGenerationStatusLabel = (status: number): string => {
  const statusMap: Record<number, string> = {
    0: '生成中',
    1: '已完成',
    2: '失败',
  }
  return statusMap[status] || '未知'
}

const getGenerationStatusClass = (status: number): string => {
  const classMap: Record<number, string> = {
    0: 'status-generating',
    1: 'status-completed',
    2: 'status-failed',
  }
  return classMap[status] || ''
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

const formatTime = (timeStr: string | null): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN')
}

const formatMessageTime = (timeStr: string): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

watch(
  () => route.params.agentId,
  (newAgentId) => {
    if (newAgentId) {
      loadAgentDetail()
      loadConversations()
      handleNewChat()
    }
  }
)

onMounted(() => {
  initDebug()
  if (agentId.value) {
    loadAgentDetail()
    loadConversations()
  }
})
</script>

<style scoped>
.chat-page {
  min-height: 100%;
  margin: -24px -32px;
}

.chat-container {
  display: flex;
  height: calc(100vh - 68px);
}

.chat-sidebar {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e5e6eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e6eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: color 0.2s ease;
}

.header-left:hover {
  color: #165DFF;
}

.back-icon {
  font-size: 16px;
  color: #4e5969;
  transition: color 0.2s ease;
}

.header-left:hover .back-icon {
  color: #165DFF;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.new-chat-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.new-chat-btn:hover {
  background: #f7f8fa;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conversation-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.conversation-item:hover {
  background: #f7f8fa;
}

.conversation-item-active {
  background: rgba(22, 93, 255, 0.08);
}

.conversation-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #165DFF 0%, #722ed1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.conversation-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #86909c;
}

.conversation-time {
  flex-shrink: 0;
}

.conversation-stage {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.stage-clarifying {
  background: #fff7e6;
  color: #ff7d00;
}

.stage-outline, .stage-template {
  background: #e8f3ff;
  color: #165DFF;
}

.stage-confirmed, .stage-completed {
  background: #e8ffea;
  color: #00b42a;
}

.stage-generating {
  background: #fff0f0;
  color: #f53f3f;
}

.empty-conversations {
  padding: 40px 20px;
}

.empty-icon {
  font-size: 48px;
  color: #c9cdd4;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f7f8fa;
}

.chat-header {
  padding: 12px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e5e6eb;
}

.chat-agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-agent-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #165DFF 0%, #722ed1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.chat-agent-detail {
  display: flex;
  flex-direction: column;
}

.chat-agent-name {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.chat-agent-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00B42A;
  animation: pulse 2s ease-in-out infinite;
}

.current-stage-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.chat-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f2f5;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #86909c;
}

.status-item.confirmed {
  color: #00b42a;
}

.status-icon {
  font-size: 14px;
}

.status-icon.confirmed {
  color: #00b42a;
}

.status-icon.pending {
  color: #c9cdd4;
}

.status-divider {
  width: 40px;
  height: 1px;
  background: #e5e6eb;
}

.status-text {
  white-space: nowrap;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.welcome-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.welcome-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, #165DFF 0%, #722ed1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 12px 32px rgba(22, 93, 255, 0.3);
}

.welcome-icon {
  font-size: 40px;
  color: white;
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 12px 0;
}

.welcome-desc {
  font-size: 14px;
  color: #86909c;
  max-width: 400px;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 500px;
  width: 100%;
}

.quick-action-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action-card:hover {
  border-color: #165DFF;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.1);
  transform: translateY(-2px);
}

.quick-action-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #E8F3FF 0%, #D0E8FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #165DFF;
  font-size: 16px;
  flex-shrink: 0;
}

.quick-action-text {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  text-align: left;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
  font-weight: 600;
}

.agent-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
}

.message-content {
  max-width: 70%;
}

.message-user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-sender {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 6px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
}

.message-assistant .message-bubble {
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-bottom-left-radius: 4px;
}

.message-user .message-bubble {
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-text {
  font-size: 14px;
  word-break: break-word;
  line-height: 1.7;
}

.message-text.markdown-content :deep(h1) {
  font-size: 18px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  color: #1d2129;
}

.message-text.markdown-content :deep(h2) {
  font-size: 16px;
  font-weight: 600;
  margin: 10px 0 6px 0;
  color: #1d2129;
}

.message-text.markdown-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 8px 0 4px 0;
  color: #1d2129;
}

.message-text.markdown-content :deep(p) {
  margin: 6px 0;
}

.message-text.markdown-content :deep(ul),
.message-text.markdown-content :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.message-text.markdown-content :deep(li) {
  margin: 4px 0;
}

.message-text.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1d2129;
}

.message-text.markdown-content :deep(em) {
  font-style: italic;
}

.message-text.markdown-content :deep(code) {
  background: #f2f3f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #f53f3f;
}

.message-text.markdown-content :deep(pre) {
  background: #f7f8fa;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #1d2129;
}

.message-text.markdown-content :deep(blockquote) {
  border-left: 3px solid #165dff;
  padding-left: 12px;
  margin: 8px 0;
  color: #4e5969;
}

.message-text.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #e5e6eb;
  margin: 12px 0;
}

.message-text.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-text.markdown-content :deep(th),
.message-text.markdown-content :deep(td) {
  border: 1px solid #e5e6eb;
  padding: 8px 12px;
  text-align: left;
}

.message-text.markdown-content :deep(th) {
  background: #f7f8fa;
  font-weight: 600;
}

.message-time {
  font-size: 11px;
  color: #c9cdd4;
  margin-top: 6px;
}

.typing-bubble {
  padding: 16px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #165DFF;
  animation: typing 1.4s ease-in-out infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { 
    transform: translateY(0);
    opacity: 0.4;
  }
  30% { 
    transform: translateY(-6px);
    opacity: 1;
  }
}

.chat-action-bar {
  padding: 12px 24px;
  background: #ffffff;
  border-top: 1px solid #e5e6eb;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.confirm-btn {
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  border: none;
  color: white;
}

.confirm-btn:hover {
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
  color: white;
}

.revise-btn {
  background: #ffffff;
  border: 1px solid #e5e6eb;
  color: #1d2129;
}

.revise-btn:hover {
  border-color: #165DFF;
  color: #165DFF;
}

.generate-btn {
  background: linear-gradient(135deg, #00b42a 0%, #23c34b 100%);
  border: none;
  color: white;
}

.generate-btn:hover {
  box-shadow: 0 4px 12px rgba(0, 180, 42, 0.3);
  color: white;
}

.chat-input-area {
  padding: 16px 24px;
  background: #ffffff;
  border-top: 1px solid #e5e6eb;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f7f8fa;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  padding: 12px 16px;
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: #165DFF;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.08);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  padding: 0;
}

.chat-input:focus {
  outline: none;
  box-shadow: none;
}

.input-actions {
  flex-shrink: 0;
}

.input-tip {
  text-align: center;
  font-size: 12px;
  color: #c9cdd4;
  margin-top: 8px;
}

.generated-files-section {
  padding: 16px 24px;
  background: #fffbe6;
  border-top: 1px solid #ffeb3b;
}

.files-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.files-count {
  font-size: 12px;
  color: #86909c;
  margin-left: 4px;
}

.files-icon {
  font-size: 18px;
  color: #ff7d00;
}

.files-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-radius: 12px;
}

.file-item-failed {
  background: #fff5f5;
  border-color: #ffcccc;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-type-icon {
  font-size: 24px;
  color: #165dff;
  flex-shrink: 0;
}

.file-type-icon-failed {
  color: #f53f3f;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-template {
  font-size: 12px;
  color: #86909c;
  margin-left: 4px;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.file-size {
  color: #86909c;
}

.file-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.file-time {
  color: #c9cdd4;
}

.status-generating {
  background: #e8f3ff;
  color: #165dff;
}

.status-completed {
  background: #e8ffea;
  color: #00b42a;
}

.status-failed {
  background: #fff0f0;
  color: #f53f3f;
}

.file-version {
  color: #86909c;
}

.file-error {
  margin-top: 8px;
}

.error-alert {
  border-radius: 8px;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.download-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
}

@media (max-width: 1024px) {
  .chat-sidebar {
    width: 240px;
  }
  
  .quick-actions {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .chat-page {
    margin: -16px;
  }
  
  .chat-sidebar {
    position: fixed;
    left: 0;
    top: 68px;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .chat-sidebar.open {
    transform: translateX(0);
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
  
  .action-btn {
    flex: 1;
    min-width: 120px;
    justify-content: center;
  }
}
</style>
