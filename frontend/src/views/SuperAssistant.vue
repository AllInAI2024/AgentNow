<template>
  <MainLayout>
    <div class="assistant-page">
      <div class="assistant-container">
        <div class="assistant-sidebar">
          <div class="sidebar-header">
            <div class="sidebar-title">
              <MessageOutlined class="title-icon" />
              <span>超级助理</span>
            </div>
            <a-button type="text" class="new-chat-btn" @click="handleNewSession">
              <PlusOutlined />
            </a-button>
          </div>

          <div class="sidebar-content">
            <a-spin :spinning="loadingSessions">
              <div v-if="sessions.length > 0" class="session-list">
                <div
                  v-for="s in sessions"
                  :key="s.session_id"
                  class="session-item"
                  :class="{ active: currentSessionId === s.session_id }"
                  @click="handleSelectSession(s.session_id)"
                >
                  <div class="session-icon">
                    <MessageOutlined />
                  </div>
                  <div class="session-info">
                    <div class="session-title">{{ s.title || '新对话' }}</div>
                    <div class="session-meta">
                      <span class="session-time">{{ formatTime(s.updated_at || s.created_at) }}</span>
                      <span class="session-count">{{ s.message_count }}</span>
                    </div>
                  </div>
                  <a-dropdown :trigger="['click']" placement="bottomRight">
                    <a-button type="text" size="small" class="session-more" @click.stop>
                      <MoreOutlined />
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="delete" danger @click="handleDeleteSession(s.session_id)">
                          删除
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </div>

              <a-empty v-else-if="!loadingSessions" description="暂无对话，开始新对话吧" />
            </a-spin>
          </div>
        </div>

        <div class="assistant-main">
          <div class="assistant-header">
            <div class="assistant-header-left">
              <div class="assistant-badge">
                <RobotOutlined />
              </div>
              <div class="assistant-header-text">
                <div class="assistant-name">Hermes 对话</div>
                <div class="assistant-sub">基于当前登录人自动绑定 Profile</div>
              </div>
            </div>
            <div class="assistant-header-right">
              <div class="header-control">
                <span class="control-label">工作区</span>
                <a-select
                  v-model:value="selectedWorkspace"
                  class="control-select"
                  placeholder="选择工作区"
                  :options="workspaceOptions"
                  :loading="loadingWorkspaces"
                  show-search
                  :filter-option="filterWorkspaceOption"
                  @change="handleWorkspaceChange"
                />
              </div>
              <div class="header-control">
                <span class="control-label">模型</span>
                <a-select
                  v-model:value="selectedModel"
                  class="control-select"
                  placeholder="选择模型"
                  :options="modelOptions"
                  :loading="loadingModels"
                  show-search
                  :filter-option="filterModelOption"
                />
              </div>
              <div class="header-control reasoning-control">
                <span class="control-label">思考</span>
                <a-select v-model:value="selectedReasoning" class="control-select" :options="reasoningOptions" />
              </div>
            </div>
          </div>

          <div class="assistant-messages" ref="messagesContainer">
            <a-spin :spinning="loadingSession">
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
                      <div class="assistant-avatar">
                        <RobotOutlined />
                      </div>
                    </template>
                  </div>
                  <div class="message-content">
                    <div class="message-bubble" :class="getBubbleClass(msg)">
                      <div
                        v-if="msg.role === 'assistant'"
                        class="message-text markdown-content"
                        v-html="renderAssistantHtml(msg.content)"
                      ></div>
                      <div v-else class="message-text">{{ msg.content }}</div>
                    </div>
                  </div>
                </div>
              </template>

              <div v-else class="welcome-section" v-if="!loadingSession">
                <div class="welcome-icon">
                  <RobotOutlined />
                </div>
                <div class="welcome-title">你好，我是超级助理</div>
                <div class="welcome-desc">直接输入问题开始对话</div>
              </div>

              <div v-if="isTyping" class="message-wrapper message-assistant typing-row">
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

          <div class="assistant-composer">
            <div v-if="pendingFiles.length > 0" class="attachment-tray">
              <a-tag
                v-for="f in pendingFiles"
                :key="f.path"
                closable
                class="attachment-tag"
                @close="removePendingFile(f.path)"
              >
                {{ f.name }}
              </a-tag>
              <a-button type="link" class="clear-attachments" @click="clearPendingFiles">清空</a-button>
            </div>
            <div class="composer-row">
              <a-button class="attach-icon-btn" @click="triggerFilePick" :loading="uploading" :disabled="sending">
                <PaperClipOutlined />
              </a-button>
              <div class="composer-input">
                <a-textarea
                  v-model:value="inputMessage"
                  placeholder="输入消息，Enter 发送，Shift+Enter 换行"
                  :auto-size="{ minRows: 3, maxRows: 10 }"
                  :disabled="sending"
                  @keydown="handleKeydown"
                />
              </div>
              <a-button
                v-if="!sending"
                type="primary"
                class="send-btn"
                :disabled="!canSend"
                @click="handleSend"
              >
                <SendOutlined />
              </a-button>
              <a-button
                v-else
                danger
                class="send-btn"
                @click="handleCancel"
              >
                <StopOutlined />
              </a-button>
            </div>
            <input ref="fileInput" type="file" multiple style="display:none" @change="handleFilePicked" />
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onBeforeUnmount, h } from 'vue'
import { message as toast, Modal, Input } from 'ant-design-vue'
import { marked } from 'marked'
import { MessageOutlined, PlusOutlined, SendOutlined, StopOutlined, RobotOutlined, MoreOutlined, PaperClipOutlined } from '@ant-design/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { useUserStore } from '@/stores/user'
import { superAssistantApi } from '@/api/superAssistant'
import type {
  SuperAssistantSessionListItem,
  SuperAssistantMessage,
  SuperAssistantModelListItem,
  SuperAssistantUploadResponse,
  SuperAssistantWorkspaceItem,
} from '@/types'

const userStore = useUserStore()

const sessions = ref<SuperAssistantSessionListItem[]>([])
const loadingSessions = ref(false)
const loadingSession = ref(false)

const currentSessionId = ref<string | null>(null)
const messages = ref<SuperAssistantMessage[]>([])

const inputMessage = ref('')
const sending = ref(false)
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const models = ref<SuperAssistantModelListItem[]>([])
const loadingModels = ref(false)
const selectedModel = ref<string>('')
const selectedReasoning = ref<string>('medium')
const pendingFiles = ref<SuperAssistantUploadResponse[]>([])
const uploading = ref(false)

const workspaces = ref<SuperAssistantWorkspaceItem[]>([])
const loadingWorkspaces = ref(false)
const selectedWorkspace = ref<string>('')

let streamAbort: AbortController | null = null
const activeStreamId = ref<string | null>(null)
const cancelRequested = ref(false)
const activeAssistantMsg = ref<SuperAssistantMessage | null>(null)

marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderMarkdown = (content: string | null | undefined): string => {
  if (!content) return ''
  try {
    return marked.parse(content) as string
  } catch {
    return content || ''
  }
}

const normalizeText = (content: string | null | undefined) => {
  let s = String(content || '').replace(/\u200b/g, '')
  s = s.replace(/Fatal Python error:[\s\S]*$/i, '').trim()
  s = s.replace(/^\s*┊\s*review diff[\s\S]*?(?=\n\s*⚠️|\n\s*PPT\s+已创建完成|\n\s*$)/gm, '').trim()
  s = s.replace(/^\s*⚠️\s*DANGEROUS COMMAND:[\s\S]*?(?=\n\s*PPT\s+已创建完成|\n\s*$)/gm, '').trim()
  s = s.replace(/^\s*Choice\s*\[o\/s\/a\/D\]:.*$/gmi, '').trim()
  s = s.replace(/^\s*⏱\s*Timeout\s*-.*$/gmi, '').trim()
  return s.trim()
}

const splitAssistantParts = (content: string | null | undefined): { thinking: string; conclusion: string } => {
  const t = normalizeText(content)
  if (!t) return { thinking: '', conclusion: '' }

  const paragraphs = t.split(/\n\s*\n+/).map(s => s.trim()).filter(Boolean)
  const processRe =
    /(^|\n)\s*(我来|我会|我将|我先|我通过|我正在|我打算|我准备|我需要|我再|我继续|我尝试|正在|让我|接下来|然后|先从|开始|准备|搜索|查找|分析|整理|规划|生成|制作|下面我|第一步|第二步|第三步|下一步)\b/
  const conclusionRe =
    /已完成|保存至|已保存至|输出结果|最终结果|生成完成|文件名|下载|路径[:：]|共\d+\s*页|https?:\/\/|\/Users\/|[A-Za-z]:\\|\/[^ \n]+?\.(pptx|ppt|pdf|docx|xlsx|xls|html|zip)\b/i

  const thinkingParts: string[] = []
  const conclusionParts: string[] = []

  for (const p of paragraphs) {
    if (processRe.test(p) || /(未找到|正在|准备|接下来|下一步|我会|我将|我通过).*(搜索|查找|获取|分析|整理|生成|制作)/.test(p)) {
      thinkingParts.push(p)
      continue
    }
    if (conclusionRe.test(p)) {
      conclusionParts.push(p)
      continue
    }
    conclusionParts.push(p)
  }

  if (conclusionParts.length === 0) {
    return { thinking: t, conclusion: '' }
  }
  return { thinking: thinkingParts.join('\n\n'), conclusion: conclusionParts.join('\n\n') }
}

const renderAssistantHtml = (content: string | null | undefined): string => {
  const { thinking, conclusion } = splitAssistantParts(content)
  if (!conclusion) return renderMarkdown(thinking)
  if (!thinking) return renderMarkdown(conclusion)
  const thinkingHtml = renderMarkdown(thinking)
  const conclusionHtml = renderMarkdown(conclusion)
  return `
    <details class="assistant-thinking-details">
      <summary>思考过程</summary>
      <div class="assistant-thinking-body markdown-content">${thinkingHtml}</div>
    </details>
    <div class="assistant-conclusion-body markdown-content">${conclusionHtml}</div>
  `
}

const isUserCancelledMessage = (msg: SuperAssistantMessage) => {
  return msg.role === 'assistant' && (msg.content || '').trim() === '已由用户主动终止。'
}

const getAssistantVariant = (content: string | null | undefined): 'thinking' | 'conclusion' | null => {
  const t = normalizeText(content)
  if (!t) return null
  const parts = splitAssistantParts(t)
  if (parts.thinking && parts.conclusion) return 'conclusion'
  if (parts.conclusion) return 'conclusion'
  return 'thinking'
}

const getBubbleClass = (msg: SuperAssistantMessage) => {
  const muted = isUserCancelledMessage(msg)
  if (msg.role !== 'assistant') return { 'message-bubble-muted': muted }
  const v = getAssistantVariant(msg.content)
  return {
    'message-bubble-muted': muted,
    'message-bubble-thinking': v !== 'conclusion',
    'message-bubble-conclusion': v === 'conclusion',
  }
}

const canSend = computed(() => {
  return !sending.value && (inputMessage.value.trim().length > 0 || pendingFiles.value.length > 0)
})

const scrollToBottom = async () => {
  await nextTick()
  const el = messagesContainer.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

const formatTime = (ts: number) => {
  const d = new Date(ts * 1000)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const res = await superAssistantApi.listSessions()
    sessions.value = res.data?.items || []
  } finally {
    loadingSessions.value = false
  }
}

const loadSession = async (sessionId: string) => {
  if (streamAbort) {
    streamAbort.abort()
    streamAbort = null
  }
  loadingSession.value = true
  try {
    const res = await superAssistantApi.getSession(sessionId)
    currentSessionId.value = sessionId
    const raw = (res.data?.messages || []).filter(m => normalizeText(m?.content).length > 0)
    const merged: SuperAssistantMessage[] = []
    for (const m of raw) {
      const last = merged.length > 0 ? merged[merged.length - 1] : null
      if (m.role === 'assistant' && last && last.role === 'assistant') {
        const sep = last.content && !String(last.content).endsWith('\n') ? '\n' : ''
        last.content = `${last.content || ''}${sep}${m.content || ''}`
        last.ts = m.ts
      } else {
        merged.push({ ...m })
      }
    }
    messages.value = merged
    await scrollToBottom()
  } finally {
    loadingSession.value = false
  }
}

const reasoningOptions = [
  { value: 'none', label: '无' },
  { value: 'minimal', label: '极低' },
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
  { value: 'xhigh', label: '极高' },
]

const modelOptions = computed(() => {
  return models.value.map(m => ({ value: m.id, label: m.id }))
})

const workspaceOptions = computed(() => {
  const opts = workspaces.value.map(w => ({ value: w.path, label: `${w.name} · ${w.path}` }))
  opts.push({ value: '__custom__', label: '自定义路径...' })
  return opts
})

const filterModelOption = (input: string, option: any) => {
  const v = String(option?.value || '')
  return v.toLowerCase().includes(String(input || '').toLowerCase())
}

const filterWorkspaceOption = (input: string, option: any) => {
  const v = String(option?.label || option?.value || '')
  return v.toLowerCase().includes(String(input || '').toLowerCase())
}

const loadWorkspaces = async () => {
  loadingWorkspaces.value = true
  try {
    const res = await superAssistantApi.listWorkspaces()
    workspaces.value = res.data?.items || []
    const current = String(res.data?.current || '').trim()
    const fallback = String(res.data?.default || '').trim()
    selectedWorkspace.value = current || fallback || (workspaces.value[0]?.path || '')
    try {
      if (selectedWorkspace.value) localStorage.setItem('super_assistant_workspace', selectedWorkspace.value)
    } catch {}
  } catch {
    workspaces.value = []
  } finally {
    loadingWorkspaces.value = false
  }
}

const handleWorkspaceChange = async (val: string) => {
  const v = String(val || '').trim()
  const prev = selectedWorkspace.value
  if (!v) return
  if (v === '__custom__') {
    const customPath = ref<string>(prev || '')
    Modal.confirm({
      title: '自定义工作区路径',
      content: () =>
        h('div', { style: 'margin-top: 8px' }, [
          h(Input, {
            value: customPath.value,
            placeholder: '请输入工作区路径（会自动创建目录）',
            'onUpdate:value': (nv: string) => (customPath.value = nv),
          }),
        ]),
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        const p = String(customPath.value || '').trim()
        if (!p) {
          toast.error('请输入工作区路径')
          selectedWorkspace.value = prev
          return
        }
        const resp = await superAssistantApi.selectWorkspace(p)
        workspaces.value = resp.data?.items || []
        selectedWorkspace.value = String(resp.data?.current || p).trim()
        try {
          if (selectedWorkspace.value) localStorage.setItem('super_assistant_workspace', selectedWorkspace.value)
        } catch {}
      },
      onCancel: () => {
        selectedWorkspace.value = prev
      },
    })
    return
  }
  try {
    const resp = await superAssistantApi.selectWorkspace(v)
    workspaces.value = resp.data?.items || []
    selectedWorkspace.value = String(resp.data?.current || v).trim()
    try {
      if (selectedWorkspace.value) localStorage.setItem('super_assistant_workspace', selectedWorkspace.value)
    } catch {}
  } catch (e) {
    selectedWorkspace.value = prev
    toast.error(String((e as Error)?.message || '设置工作区失败'))
  }
}

const loadModels = async () => {
  loadingModels.value = true
  try {
    const res = await superAssistantApi.listModels()
    models.value = res.data?.models || []
    const stored = localStorage.getItem('super_assistant_model') || ''
    if (stored && models.value.some(m => m.id === stored)) {
      selectedModel.value = stored
    } else if (models.value.length > 0) {
      selectedModel.value = models.value[0].id
    }
  } catch {
    models.value = []
  } finally {
    loadingModels.value = false
  }
}

const persistPrefs = () => {
  try {
    if (selectedModel.value) localStorage.setItem('super_assistant_model', selectedModel.value)
    if (selectedReasoning.value) localStorage.setItem('super_assistant_reasoning', selectedReasoning.value)
  } catch {}
}

const restorePrefs = () => {
  try {
    const r = localStorage.getItem('super_assistant_reasoning')
    if (r) selectedReasoning.value = r
  } catch {}
}

const triggerFilePick = () => {
  if (!fileInput.value) return
  fileInput.value.value = ''
  fileInput.value.click()
}

const handleFilePicked = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return
  uploading.value = true
  try {
    for (const f of files) {
      const res = await superAssistantApi.upload(currentSessionId.value, f)
      pendingFiles.value.push(res.data)
    }
  } catch {
    toast.error('附件上传失败')
  } finally {
    uploading.value = false
  }
}

const removePendingFile = (path: string) => {
  pendingFiles.value = pendingFiles.value.filter(f => f.path !== path)
}

const clearPendingFiles = () => {
  pendingFiles.value = []
}

const handleNewSession = async () => {
  currentSessionId.value = null
  messages.value = []
  pendingFiles.value = []
}

const handleSelectSession = async (sessionId: string) => {
  if (sessionId === currentSessionId.value) return
  await loadSession(sessionId)
}

const handleDeleteSession = async (sessionId: string) => {
  try {
    await superAssistantApi.deleteSession(sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
    await loadSessions()
  } catch {
    toast.error('删除失败')
  }
}

const parseSseEvent = (raw: string): Array<{ event: string; data: string }> => {
  const blocks = raw.split('\n\n').filter(Boolean)
  const out: Array<{ event: string; data: string }> = []
  for (const b of blocks) {
    const lines = b.split('\n')
    let event = 'message'
    const dataLines: string[] = []
    for (const line of lines) {
      if (line.startsWith(':')) continue
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }
    out.push({ event, data: dataLines.join('\n') })
  }
  return out
}

const streamChat = async (streamId: string, onDelta: (text: string) => void): Promise<string | null> => {
  if (streamAbort) streamAbort.abort()
  streamAbort = new AbortController()

  const token = userStore.token
  const resp = await fetch(`/api/v1/assistant/chat/stream?stream_id=${encodeURIComponent(streamId)}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: streamAbort.signal,
  })
  if (!resp.ok || !resp.body) {
    throw new Error('stream failed')
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finalSessionId: string | null = null

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      while (true) {
        const idx = buffer.indexOf('\n\n')
        if (idx === -1) break
        const chunk = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        const events = parseSseEvent(chunk + '\n\n')
        for (const evt of events) {
          if (evt.event === 'delta') {
            if (cancelRequested.value) continue
            try {
              const payload = JSON.parse(evt.data)
              onDelta(String(payload.text || ''))
            } catch {
              onDelta(evt.data)
            }
          } else if (evt.event === 'error') {
            let msg = '对话失败'
            try {
              const payload = JSON.parse(evt.data)
              msg = String(payload.message || msg)
            } catch {}
            throw new Error(msg)
          } else if (evt.event === 'cancel') {
            throw new Error('已中断')
          } else if (evt.event === 'done') {
            try {
              const payload = JSON.parse(evt.data)
              const sid = String(payload.session_id || '').trim()
              if (sid) finalSessionId = sid
            } catch {}
          }
        }
      }
    }
    return finalSessionId
  } catch (e) {
    const msg = String((e as Error)?.message || e)
    if (cancelRequested.value && /aborted/i.test(msg)) {
      throw new Error('已中断')
    }
    throw e
  }
}

const handleCancel = async () => {
  const sid = activeStreamId.value
  if (!sid) return
  Modal.confirm({
    title: '确认终止',
    content: '确定要终止当前对话吗？',
    okText: '终止',
    cancelText: '继续',
    okType: 'danger',
    onOk: async () => {
      cancelRequested.value = true
      if (activeAssistantMsg.value && !activeAssistantMsg.value.content) {
        activeAssistantMsg.value.content = '已由用户主动终止。'
      }
      try {
        await superAssistantApi.chatCancel(sid)
      } catch {
      } finally {
        sending.value = false
        isTyping.value = false
        activeStreamId.value = null
      }
    },
  })
}

const handleSend = async () => {
  const text = inputMessage.value.trim()
  if (!text && pendingFiles.value.length === 0) return

  sending.value = true
  isTyping.value = true
  cancelRequested.value = false
  try {
    const sid = currentSessionId.value || undefined
    const usedModel = selectedModel.value
    const usedReasoning = selectedReasoning.value
    persistPrefs()

    const attachmentPaths = pendingFiles.value.map(f => f.path)
    const finalText =
      text ||
      (attachmentPaths.length > 0
        ? `I've uploaded ${attachmentPaths.length} file(s): ${attachmentPaths.join(', ')}`
        : '')

    inputMessage.value = ''
    await nextTick()
    const localUserText =
      text ||
      (pendingFiles.value.length > 0
        ? `已上传 ${pendingFiles.value.length} 个附件：${pendingFiles.value.map(f => f.name).join('、')}`
        : '')

    const userMsg: SuperAssistantMessage = { role: 'user', content: localUserText, ts: Date.now() / 1000 }
    messages.value.push(userMsg)
    const assistantMsg: SuperAssistantMessage = { role: 'assistant', content: '', ts: Date.now() / 1000 }
    messages.value.push(assistantMsg)
    activeAssistantMsg.value = assistantMsg
    await scrollToBottom()

    const attachmentsPayload = pendingFiles.value.map(f => ({
      name: f.name,
      path: f.path,
      mime: f.mime,
      size: f.size,
      is_image: f.is_image,
    }))
    pendingFiles.value = []

    const res = await superAssistantApi.chatStart({
      session_id: sid || undefined,
      message: finalText,
      workspace: selectedWorkspace.value || undefined,
      model: usedModel || undefined,
      reasoning_effort: usedReasoning || undefined,
      attachments: attachmentsPayload,
    })
    const streamId = res.data.stream_id
    activeStreamId.value = streamId

    const newSid = await streamChat(streamId, (delta) => {
      assistantMsg.content += delta
      scrollToBottom()
    })

    isTyping.value = false
    activeStreamId.value = null
    activeAssistantMsg.value = null
    await loadSessions()
    const finalSid = (newSid || sid || '').trim()
    if (finalSid) {
      await loadSession(finalSid)
    } else {
      await loadSessions()
    }
  } catch (e) {
    isTyping.value = false
    const msg = String((e as Error)?.message || '发送失败')
    if (msg === '已中断') {
      if (activeAssistantMsg.value && !activeAssistantMsg.value.content) {
        activeAssistantMsg.value.content = '已由用户主动终止。'
      }
    } else if (!/BodyStreamBuffer was aborted/i.test(msg)) {
      toast.error(msg)
    }
    activeStreamId.value = null
    activeAssistantMsg.value = null
  } finally {
    inputMessage.value = ''
    sending.value = false
    cancelRequested.value = false
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (canSend.value) handleSend()
  }
}

onMounted(async () => {
  restorePrefs()
  await loadWorkspaces()
  await loadSessions()
  await loadModels()
  if (sessions.value.length > 0) {
    await loadSession(sessions.value[0].session_id)
  } else {
    await handleNewSession()
  }
})

onBeforeUnmount(() => {
  if (streamAbort) streamAbort.abort()
})
</script>

<style scoped>
.assistant-page {
  padding: 0;
}

.assistant-container {
  display: flex;
  gap: 16px;
  height: calc(100vh - 176px);
  min-height: 0;
}

.assistant-sidebar {
  width: 320px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 230, 235, 0.8);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px 16px;
  border-bottom: 1px solid rgba(229, 230, 235, 0.8);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.title-icon {
  color: #165dff;
}

.new-chat-btn {
  border-radius: 10px;
}

.sidebar-content {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-item:hover {
  background: rgba(22, 93, 255, 0.06);
}

.session-item.active {
  background: rgba(22, 93, 255, 0.10);
}

.session-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(22, 93, 255, 0.10);
  color: #165dff;
  flex-shrink: 0;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #86909c;
  font-size: 12px;
}

.session-count {
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(134, 144, 156, 0.14);
}

.session-more {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  color: #86909c;
}

.assistant-main {
  flex: 1;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 230, 235, 0.8);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.assistant-header {
  padding: 16px 18px;
  border-bottom: 1px solid rgba(229, 230, 235, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.assistant-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assistant-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 12px;
  color: #86909c;
}

.control-select {
  width: auto;
  min-width: 120px;
  max-width: 260px;
}

.reasoning-control .control-select {
  min-width: 72px;
  max-width: 88px;
}

.attach-icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.assistant-badge {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #165dff 0%, #4080ff 50%, #722ed1 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.assistant-name {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.assistant-sub {
  font-size: 12px;
  color: #86909c;
  margin-top: 2px;
}

.assistant-messages {
  flex: 1;
  overflow: auto;
  padding: 20px 24px 14px 24px;
  min-height: 0;
}

.welcome-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #86909c;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: rgba(22, 93, 255, 0.10);
  color: #165dff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-bottom: 14px;
}

.welcome-title {
  font-size: 18px;
  font-weight: 700;
  color: #1d2129;
}

.welcome-desc {
  margin-top: 6px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  align-items: flex-end;
  width: 100%;
}

.message-user {
  justify-content: flex-end;
}

.message-assistant {
  justify-content: flex-start;
}

.message-user .message-avatar {
  order: 2;
}

.message-user .message-content {
  order: 1;
}

.message-avatar {
  width: 44px;
  display: flex;
  justify-content: center;
  flex: 0 0 44px;
}

.assistant-avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: rgba(22, 93, 255, 0.10);
  color: #165dff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-content {
  flex: 0 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  max-width: calc(100% - 56px);
}

.message-bubble {
  border-radius: 14px;
  padding: 12px 16px;
  line-height: 1.6;
  border: 1px solid rgba(229, 230, 235, 0.8);
  background: #fff;
  max-width: 760px;
  display: inline-block;
  width: fit-content;
}

.message-bubble-thinking {
  background: rgba(134, 144, 156, 0.08);
  border-style: dashed;
  padding: 10px 14px;
}

.message-bubble-conclusion {
  border-left: 3px solid rgba(22, 93, 255, 0.65);
  padding-left: 13px;
}

.message-user .message-bubble {
  background: rgba(22, 93, 255, 0.08);
  border-color: rgba(22, 93, 255, 0.16);
}

.message-user .message-content {
  align-items: flex-end;
}

.message-user .message-bubble {
  text-align: right;
}

.message-assistant .message-content {
  align-items: flex-start;
}

.message-bubble-muted {
  opacity: 0.72;
  font-style: italic;
}

.message-text {
  font-size: 14px;
  color: #1d2129;
  word-break: break-word;
}

.message-bubble-thinking .message-text {
  font-size: 13px;
  line-height: 1.55;
  color: #4e5969;
}

.assistant-thinking-details {
  margin: 0 0 8px 0;
}

.assistant-thinking-details > summary {
  font-size: 12px;
  color: #86909c;
  cursor: pointer;
  user-select: none;
  list-style: none;
}

.assistant-thinking-details > summary::-webkit-details-marker {
  display: none;
}

.assistant-thinking-body {
  margin-top: 8px;
  color: #4e5969;
  background: rgba(134, 144, 156, 0.10);
  border: 1px dashed rgba(200, 204, 212, 0.9);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.55;
}

.assistant-thinking-body :deep(*) {
  font-size: 12px;
  line-height: 1.55;
  color: #4e5969;
}

.assistant-thinking-body :deep(h1),
.assistant-thinking-body :deep(h2),
.assistant-thinking-body :deep(h3) {
  font-size: 13px;
  margin: 10px 0 6px 0;
  color: #4e5969;
}

.assistant-thinking-body :deep(code) {
  background: rgba(242, 243, 245, 0.9);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
  color: #4e5969;
}

.assistant-conclusion-body {
  margin-top: 8px;
  color: #1d2129;
  font-size: 14px;
}

.message-text.markdown-content :deep(ul),
.message-text.markdown-content :deep(ol) {
  margin: 6px 0;
  padding-left: 1.25em;
}

.message-text.markdown-content :deep(li) {
  margin: 2px 0;
}

.message-text.markdown-content :deep(ul ul),
.message-text.markdown-content :deep(ol ol),
.message-text.markdown-content :deep(ul ol),
.message-text.markdown-content :deep(ol ul) {
  margin: 4px 0;
  padding-left: 1.25em;
}

.typing-row .message-bubble {
  background: rgba(134, 144, 156, 0.08);
  border-style: dashed;
}

.typing-bubble {
  width: 120px;
}

.typing-indicator {
  display: flex;
  gap: 6px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: #c9cdd4;
  border-radius: 50%;
  animation: typing 1.1s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.85);
    opacity: 0.6;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.assistant-composer {
  padding: 14px 16px 16px 16px;
  border-top: 1px solid rgba(229, 230, 235, 0.8);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.composer-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  min-width: 0;
}

.composer-input {
  flex: 1;
  min-width: 0;
}

.composer-input :deep(.ant-input-textarea) {
  width: 100%;
}

.composer-input :deep(.ant-input) {
  border-radius: 12px;
}

.send-btn {
  height: 40px;
  border-radius: 12px;
}

.attachment-tray {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.attachment-tag {
  border-radius: 10px;
  padding: 4px 10px;
}

.clear-attachments {
  padding: 0;
}
</style>
