<template>
  <MainLayout>
    <div class="my-agents-page">
      <div class="page-header">
        <div class="header-left">
          <RobotOutlined class="page-icon" />
          <div class="header-title">
            <h1>我的智能体</h1>
            <p class="subtitle">管理和使用您的专属智能体</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-spin :spinning="loading">
          <template v-if="agents.length > 0">
            <a-row :gutter="[24, 24]">
              <a-col :xs="24" :sm="12" :lg="8" v-for="agent in agents" :key="agent.id">
                <div class="agent-card card-hover-lift" @click="handleEnterAgent(agent)">
                  <div class="agent-card-inner">
                    <div class="agent-icon-wrapper bg-gradient-agent">
                      <AppstoreOutlined class="agent-icon" />
                    </div>
                    <div class="agent-info">
                      <h3 class="agent-name">{{ agent.display_name }}</h3>
                      <p class="agent-desc">{{ agent.template?.description || '企业智能助手' }}</p>
                      <div class="agent-status-row">
                        <a-tag :color="getAgentStatusColor(agent.agent_status)" class="agent-status-tag">
                          {{ getAgentStatusText(agent.agent_status) }}
                        </a-tag>
                        <span v-if="agent.last_used_at" class="agent-last-use">
                          最后使用: {{ formatTime(agent.last_used_at) }}
                        </span>
                      </div>
                    </div>
                    <div class="agent-arrow">
                      <RightOutlined class="arrow-icon" />
                    </div>
                  </div>
                </div>
              </a-col>
            </a-row>
          </template>

          <template v-else-if="!loading">
            <a-card class="empty-card">
              <a-empty description="您还没有开通智能体">
                <template #image>
                  <RobotOutlined class="empty-icon" />
                </template>
                <a-button type="primary" @click="handleEnableAgent" :loading="enabling">
                  <RocketOutlined /> 立即开通智能体
                </a-button>
              </a-empty>
            </a-card>
          </template>
        </a-spin>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  RobotOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  RightOutlined,
  RocketOutlined,
} from '@ant-design/icons-vue'
import { agentApi } from '@/api/agent'
import type { UserAgent } from '@/types'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()

const loading = ref(false)
const enabling = ref(false)
const agents = ref<UserAgent[]>([])

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await agentApi.getMyAgents()
    if (response.code === 200 && response.data) {
      agents.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  loadAgents()
  message.success('已刷新')
}

const handleEnableAgent = async () => {
  enabling.value = true
  try {
    const response = await agentApi.enableAgent()
    if (response.code === 200 && response.data) {
      message.success('智能体开通成功！')
      await loadAgents()
      if (agents.value.length > 0) {
        handleEnterAgent(agents.value[0])
      }
    }
  } catch (error) {
    console.error('开通智能体失败:', error)
    message.error('开通智能体失败，请稍后重试')
  } finally {
    enabling.value = false
  }
}

const handleEnterAgent = (agent: UserAgent) => {
  if (agent.agent_status !== 1) {
    message.warning('该智能体当前不可用')
    return
  }
  router.push({ 
    name: 'AgentChat', 
    params: { agentId: String(agent.id) } 
  })
}

const getAgentStatusColor = (status: number): string => {
  const colorMap: Record<number, string> = {
    0: 'default',
    1: 'green',
    2: 'default',
    3: 'red',
  }
  return colorMap[status] || 'default'
}

const getAgentStatusText = (status: number): string => {
  const textMap: Record<number, string> = {
    0: '待开通',
    1: '可用',
    2: '已停用',
    3: '开通失败',
  }
  return textMap[status] || '未知'
}

const formatTime = (timeStr: string): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.my-agents-page {
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-icon {
  font-size: 32px;
  color: #165DFF;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
  line-height: 1.4;
}

.subtitle {
  font-size: 14px;
  color: #86909c;
  margin: 4px 0 0 0;
}

.page-content {
  padding: 0;
}

.empty-card {
  padding: 60px 24px;
}

.empty-icon {
  font-size: 72px;
  color: #c9cdd4;
}

.agent-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid #e5e6eb;
  transition: all 0.3s ease;
}

.card-hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
  border-color: rgba(22, 93, 255, 0.3);
}

.agent-card-inner {
  padding: 24px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.agent-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.2);
  flex-shrink: 0;
}

.bg-gradient-agent {
  background: linear-gradient(135deg, #165DFF 0%, #722ed1 100%);
}

.agent-icon {
  font-size: 28px;
  color: white;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-size: 16px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 8px 0;
  transition: color 0.2s ease;
}

.agent-card:hover .agent-name {
  color: #165DFF;
}

.agent-desc {
  font-size: 13px;
  color: #86909c;
  margin: 0 0 12px 0;
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.agent-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.agent-status-tag {
  border: none;
  font-weight: 500;
  padding: 2px 8px;
  font-size: 12px;
}

.agent-last-use {
  font-size: 12px;
  color: #c9cdd4;
}

.agent-arrow {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f7f8fa;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.agent-card:hover .agent-arrow {
  background: #165DFF;
}

.arrow-icon {
  font-size: 14px;
  color: #86909c;
  transition: transform 0.3s ease, color 0.3s ease;
}

.agent-card:hover .arrow-icon {
  color: white;
  transform: translateX(2px);
}
</style>
