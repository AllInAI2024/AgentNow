<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <FolderOpenOutlined class="page-icon" />
          <div class="header-title">
            <h1>记忆系统</h1>
            <p class="subtitle">各 Profile 记忆内容与使用状态</p>
          </div>
        </div>
        <div class="header-right">
          <a-select
            v-model:value="selectedProfile"
            placeholder="选择 Profile"
            style="width: 200px"
            :loading="loadingList"
            @change="handleProfileChange"
          >
            <a-select-option
              v-for="item in profileList"
              :key="item.profile_name"
              :value="item.profile_name"
            >
              <div class="profile-option">
                <span class="profile-name">{{ item.display_name }}</span>
                <span v-if="item.user_name" class="profile-user">
                  ({{ item.user_name }})
                </span>
              </div>
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
        </div>

        <template v-else-if="memoryData">
          <div class="status-cards">
            <a-card class="status-card memory-card">
              <div class="card-header">
                <div class="card-title">
                  <BookOutlined class="card-icon" />
                  <span>Agent 笔记</span>
                  <a-tag color="blue">{{ memoryData.memory_file.name }}</a-tag>
                </div>
                <div class="card-status" :class="getProgressStatus(memoryData.memory_file.progress)">
                  <span :class="getStatusClass(memoryData.memory_file.progress)">
                    {{ getStatusText(memoryData.memory_file.progress) }}
                  </span>
                </div>
              </div>

              <div class="progress-section">
                <div class="progress-header">
                  <span class="progress-label">字符使用</span>
                  <span class="progress-value">
                    {{ formatNumber(memoryData.memory_file.current_chars) }} / 
                    {{ formatNumber(memoryData.memory_file.char_limit) }}
                  </span>
                </div>
                <a-progress
                  :percent="memoryData.memory_file.progress"
                  :stroke-color="getProgressColor(memoryData.memory_file.progress)"
                  :show-info="false"
                  :stroke-width="12"
                />
              </div>

              <div class="stats-row">
                <div class="stat-item">
                  <span class="stat-label">条目数</span>
                  <span class="stat-value">{{ memoryData.memory_file.item_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">最后更新</span>
                  <span class="stat-value">
                    {{ formatTime(memoryData.memory_file.last_updated) }}
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">文件状态</span>
                  <span class="stat-value">
                    <a-tag :color="memoryData.memory_file.exists ? 'green' : 'default'">
                      {{ memoryData.memory_file.exists ? '已存在' : '未创建' }}
                    </a-tag>
                  </span>
                </div>
              </div>

              <div class="card-description">
                <InfoCircleOutlined class="desc-icon" />
                <span>{{ memoryData.memory_file.description }}</span>
              </div>
            </a-card>

            <a-card class="status-card user-card">
              <div class="card-header">
                <div class="card-title">
                  <UserOutlined class="card-icon" />
                  <span>用户画像</span>
                  <a-tag color="orange">{{ memoryData.user_file.name }}</a-tag>
                </div>
                <div class="card-status" :class="getProgressStatus(memoryData.user_file.progress)">
                  <span :class="getStatusClass(memoryData.user_file.progress)">
                    {{ getStatusText(memoryData.user_file.progress) }}
                  </span>
                </div>
              </div>

              <div class="progress-section">
                <div class="progress-header">
                  <span class="progress-label">字符使用</span>
                  <span class="progress-value">
                    {{ formatNumber(memoryData.user_file.current_chars) }} / 
                    {{ formatNumber(memoryData.user_file.char_limit) }}
                  </span>
                </div>
                <a-progress
                  :percent="memoryData.user_file.progress"
                  :stroke-color="getProgressColor(memoryData.user_file.progress)"
                  :show-info="false"
                  :stroke-width="12"
                />
              </div>

              <div class="stats-row">
                <div class="stat-item">
                  <span class="stat-label">条目数</span>
                  <span class="stat-value">{{ memoryData.user_file.item_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">最后更新</span>
                  <span class="stat-value">
                    {{ formatTime(memoryData.user_file.last_updated) }}
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">文件状态</span>
                  <span class="stat-value">
                    <a-tag :color="memoryData.user_file.exists ? 'green' : 'default'">
                      {{ memoryData.user_file.exists ? '已存在' : '未创建' }}
                    </a-tag>
                  </span>
                </div>
              </div>

              <div class="card-description">
                <InfoCircleOutlined class="desc-icon" />
                <span>{{ memoryData.user_file.description }}</span>
              </div>
            </a-card>
          </div>

          <a-card class="content-card">
            <template #title>
              <div class="content-header">
                <FileTextOutlined class="content-icon" />
                <span>记忆内容详情</span>
              </div>
            </template>

            <a-tabs v-model:activeKey="activeTab" class="memory-tabs">
              <a-tab-pane key="memory" tab="Agent 笔记 (MEMORY.md)">
                <div v-if="memoryData.memory_file.items.length === 0" class="empty-content">
                  <a-empty description="暂无记忆条目">
                    <template #image>
                      <BookOutlined class="empty-large-icon" />
                    </template>
                  </a-empty>
                </div>

                <div v-else class="memory-items">
                  <div
                    v-for="item in memoryData.memory_file.items"
                    :key="item.id"
                    class="memory-item"
                  >
                    <div class="item-header">
                      <span class="item-index">#{{ item.id }}</span>
                      <a-tag :color="getTypeColor(item.type)">
                        {{ item.type }}
                      </a-tag>
                      <span class="item-line">行 {{ item.line_number }}</span>
                    </div>
                    <div class="item-content">
                      <pre><code>{{ item.content }}</code></pre>
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <a-tab-pane key="user" tab="用户画像 (USER.md)">
                <div v-if="memoryData.user_file.items.length === 0" class="empty-content">
                  <a-empty description="暂无用户画像条目">
                    <template #image>
                      <UserOutlined class="empty-large-icon" />
                    </template>
                  </a-empty>
                </div>

                <div v-else class="memory-items">
                  <div
                    v-for="item in memoryData.user_file.items"
                    :key="item.id"
                    class="memory-item"
                  >
                    <div class="item-header">
                      <span class="item-index">#{{ item.id }}</span>
                      <a-tag :color="getTypeColor(item.type)">
                        {{ item.type }}
                      </a-tag>
                      <span class="item-line">行 {{ item.line_number }}</span>
                    </div>
                    <div class="item-content">
                      <pre><code>{{ item.content }}</code></pre>
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <a-tab-pane key="raw_memory" tab="原始内容 (MEMORY.md)">
                <div v-if="!memoryData.memory_file.raw_content" class="empty-content">
                  <a-empty description="文件不存在或内容为空" />
                </div>
                <div v-else class="raw-content">
                  <pre><code>{{ memoryData.memory_file.raw_content }}</code></pre>
                </div>
              </a-tab-pane>

              <a-tab-pane key="raw_user" tab="原始内容 (USER.md)">
                <div v-if="!memoryData.user_file.raw_content" class="empty-content">
                  <a-empty description="文件不存在或内容为空" />
                </div>
                <div v-else class="raw-content">
                  <pre><code>{{ memoryData.user_file.raw_content }}</code></pre>
                </div>
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </template>

        <div v-else class="empty-container">
          <a-empty description="请选择一个 Profile 查看其记忆内容">
            <template #image>
              <FolderOpenOutlined class="empty-large-icon" />
            </template>
          </a-empty>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  FolderOpenOutlined,
  ReloadOutlined,
  BookOutlined,
  UserOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'
import type { 
  MemoryResponse, 
  ProfileMemoryListItem 
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

const loading = ref(false)
const loadingList = ref(false)
const profileList = ref<ProfileMemoryListItem[]>([])
const selectedProfile = ref<string>('')
const memoryData = ref<MemoryResponse | null>(null)
const activeTab = ref('memory')

const formatNumber = (num: number): string => {
  return num.toLocaleString('zh-CN')
}

const formatTime = (time: string | null | undefined): string => {
  if (!time) return '从未更新'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getProgressColor = (progress: number): string => {
  if (progress >= 90) return '#ff4d4f'
  if (progress >= 70) return '#faad14'
  return '#52c41a'
}

const getProgressStatus = (progress: number): string => {
  if (progress >= 90) return 'danger'
  if (progress >= 70) return 'warning'
  return 'normal'
}

const getStatusClass = (progress: number): string => {
  if (progress >= 90) return 'status-danger'
  if (progress >= 70) return 'status-warning'
  return 'status-normal'
}

const getStatusText = (progress: number): string => {
  if (progress >= 90) return '空间紧张'
  if (progress >= 70) return '空间充足'
  return '空间充足'
}

const getTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    '项目约定': 'blue',
    '用户偏好': 'orange',
    '环境事实': 'green',
    '技术约定': 'purple',
    '业务规则': 'cyan',
    '其他': 'default',
  }
  return colorMap[type] || 'default'
}

const fetchProfileList = async () => {
  loadingList.value = true
  try {
    const res = await hermesApi.getMemoryList()
    if (res.code === 200) {
      profileList.value = res.data.items
      if (res.data.items.length > 0 && !selectedProfile.value) {
        selectedProfile.value = res.data.items[0].profile_name
        await fetchMemoryData()
      }
    } else {
      message.error(res.message || '获取 Profile 列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch profile list:', error)
    message.error('获取 Profile 列表失败')
  } finally {
    loadingList.value = false
  }
}

const fetchMemoryData = async () => {
  if (!selectedProfile.value) return

  loading.value = true
  try {
    const res = await hermesApi.getProfileMemory(selectedProfile.value)
    if (res.code === 200) {
      memoryData.value = res.data
    } else {
      message.error(res.message || '获取记忆数据失败')
    }
  } catch (error) {
    console.error('Failed to fetch memory data:', error)
    message.error('获取记忆数据失败')
  } finally {
    loading.value = false
  }
}

const handleProfileChange = () => {
  fetchMemoryData()
}

const handleRefresh = () => {
  fetchProfileList()
  if (selectedProfile.value) {
    fetchMemoryData()
  }
}

onMounted(() => {
  fetchProfileList()
})
</script>

<style scoped>
.hermes-page {
  min-height: 100%;
  padding: 24px;
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

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.profile-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-name {
  font-weight: 500;
}

.profile-user {
  color: #86909c;
  font-size: 12px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

.empty-large-icon {
  font-size: 64px;
  color: #c9cdd4;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.status-card {
  border-radius: 12px;
}

.memory-card {
  border-left: 4px solid #165DFF;
}

.user-card {
  border-left: 4px solid #fa8c16;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.card-icon {
  font-size: 20px;
}

.memory-card .card-icon {
  color: #165DFF;
}

.user-card .card-icon {
  color: #fa8c16;
}

.card-status {
  display: flex;
  align-items: center;
}

.status-normal {
  color: #52c41a;
  font-weight: 500;
}

.status-warning {
  color: #faad14;
  font-weight: 500;
}

.status-danger {
  color: #ff4d4f;
  font-weight: 500;
}

.progress-section {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 13px;
  color: #86909c;
}

.progress-value {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}

.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #86909c;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
}

.card-description {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 13px;
  color: #86909c;
}

.desc-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.content-card {
  border-radius: 12px;
}

.content-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.content-icon {
  font-size: 18px;
  color: #165DFF;
}

.memory-tabs {
  margin-top: 16px;
}

.empty-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.memory-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.memory-item {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.memory-item:hover {
  border-color: #165DFF;
  box-shadow: 0 2px 8px rgba(22, 93, 255, 0.1);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
}

.item-index {
  font-size: 13px;
  font-weight: 600;
  color: #165DFF;
  background: #e8f3ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.item-line {
  font-size: 12px;
  color: #86909c;
}

.item-content {
  padding: 16px;
}

.item-content pre {
  margin: 0;
  padding: 0;
}

.item-content code {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #1d2129;
  white-space: pre-wrap;
  word-break: break-word;
}

.raw-content {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.raw-content pre {
  margin: 0;
  padding: 0;
}

.raw-content code {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 1200px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
}
</style>
