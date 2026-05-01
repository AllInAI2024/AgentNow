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
                      <div class="message-text">{{ msg.content }}</div>
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

          <div class="chat-action-bar" v-if="showActionButtons">
            <div class="action-buttons">
              <a-button 
                type="primary" 
                size="large"
                class="action-btn confirm-btn"
                v-if="canConfirmOutline"
                @click="handleConfirmOutline"
              >
                <CheckOutlined /> 确认大纲
              </a-button>
              <a-button 
                size="large"
                class="action-btn revise-btn"
                v-if="canReviseOutline"
                @click="handleReviseOutline"
              >
                <EditOutlined /> 调整大纲
              </a-button>
              <a-button 
                type="primary" 
                size="large"
                class="action-btn confirm-btn"
                v-if="canConfirmTemplate"
                @click="handleConfirmTemplate"
              >
                <CheckOutlined /> 确认模板
              </a-button>
              <a-button 
                type="primary" 
                size="large"
                class="action-btn generate-btn"
                v-if="canGeneratePPT"
                @click="handleGeneratePPT"
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
                :rows="1"
                :auto-size="{ minRows: 1, maxRows: 4 }"
                class="chat-input"
                @keydown.enter="handleKeyDown"
                :disabled="!currentAgent || isTyping"
              />
              <div class="input-actions">
                <a-button
                  type="primary"
                  shape="circle"
                  :disabled="!inputMessage.trim() || isTyping || !currentAgent"
                  :loading="isTyping"
                  @click="handleSendMessage"
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
} from '@ant-design/icons-vue'
import { agentApi } from '@/api/agent'
import type { 
  UserAgent, 
  AgentConversation, 
  ChatMessage,
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
const inputMessage = ref('')
const loadingConversations = ref(false)
const loadingMessages = ref(false)
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const quickActions = computed(() => [
  { text: '帮我写一个公司介绍的 10 页 PPT', icon: 'file' },
  { text: '帮我做一份产品宣讲 PPT', icon: 'bulb' },
  { text: '我需要一份客户拜访汇报', icon: 'thunderbolt' },
])

const showActionButtons = computed(() => {
  if (!currentConversation.value) return false
  const stage = currentConversation.value.current_stage
  return ['outline_draft', 'outline_confirmed', 'template_select', 'final_generating'].includes(stage)
})

const canConfirmOutline = computed(() => {
  return currentConversation.value?.current_stage === 'outline_draft'
})

const canReviseOutline = computed(() => {
  return currentConversation.value?.current_stage === 'outline_draft'
})

const canConfirmTemplate = computed(() => {
  return currentConversation.value?.current_stage === 'template_select'
})

const canGeneratePPT = computed(() => {
  return currentConversation.value?.current_stage === 'final_generating'
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
    'outline_draft': '大纲草拟',
    'outline_confirmed': '大纲已确认',
    'template_select': '选择模板',
    'final_generating': '生成中',
    'completed': '已完成',
    'chatting': '对话中',
  }
  return stageMap[stage || 'chatting'] || '对话中'
}

const getStageClass = (stage: string | null | undefined): string => {
  const classMap: Record<string, string> = {
    'welcome': 'stage-welcome',
    'clarifying': 'stage-clarifying',
    'outline_draft': 'stage-outline',
    'outline_confirmed': 'stage-confirmed',
    'template_select': 'stage-template',
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
  try {
    const response = await agentApi.getConversationDetail(agentId.value, conversationId)
    if (response.code === 200 && response.data) {
      currentConversation.value = response.data.conversation
      messages.value = response.data.messages || []
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('获取会话详情失败:', error)
    message.error('加载对话失败')
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
  inputMessage.value = ''
}

const handleSelectConversation = (conv: AgentConversation) => {
  currentConversationId.value = conv.id
  loadConversationDetail(conv.id)
}

const handleQuickAction = (action: { text: string; icon: string }) => {
  inputMessage.value = action.text
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessageWithAction = async (msg: string, actionType: string = 'message') => {
  if (!currentAgent.value || isTyping.value) return

  if (msg && msg.trim()) {
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

      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    message.error('发送消息失败，请稍后重试')
    if (msg && msg.trim()) {
      messages.value = messages.value.slice(0, -1)
    }
  } finally {
    isTyping.value = false
  }
}

const handleSendMessage = async () => {
  const msg = inputMessage.value.trim()
  if (!msg) return
  await sendMessageWithAction(msg, 'message')
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
  await sendMessageWithAction('确认，生成正式 PPT', 'confirm_generation')
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
  white-space: pre-wrap;
  word-break: break-word;
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
