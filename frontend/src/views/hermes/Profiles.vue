<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <ApartmentOutlined class="page-icon" />
          <div class="header-title">
            <h1>Profiles 管理</h1>
            <p class="subtitle">Hermes 多实例管理与状态监控</p>
          </div>
        </div>
        <div class="header-right">
          <a-space>
            <a-tooltip title="运行中">
              <a-tag color="success" class="status-tag">
                <PlayCircleOutlined /> {{ profileStats.running }}
              </a-tag>
            </a-tooltip>
            <a-tooltip title="已停止">
              <a-tag color="default" class="status-tag">
                <PauseCircleOutlined /> {{ profileStats.stopped }}
              </a-tag>
            </a-tooltip>
            <a-tooltip title="异常">
              <a-tag color="error" class="status-tag">
                <ExclamationCircleOutlined /> {{ profileStats.error }}
              </a-tag>
            </a-tooltip>
          </a-space>
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <div class="content-layout">
          <div class="main-area">
            <a-card :bordered="false" class="content-card">
              <template #title>
                <div class="card-header">
                  <div class="card-title-left">
                    <AppstoreOutlined class="card-icon" />
                    <span>Profile 列表</span>
                    <span class="profile-stats">
                      (共 <span class="stat-total">{{ profileStats.total }}</span> 个)
                    </span>
                  </div>
                  <div class="card-title-right">
                    <a-space>
                      <a-select 
                        v-model:value="filterStatus" 
                        placeholder="筛选状态" 
                        style="width: 140px"
                        allow-clear
                        @change="handleFilterChange"
                      >
                        <a-select-option value="running">运行中</a-select-option>
                        <a-select-option value="starting">启动中</a-select-option>
                        <a-select-option value="stopped">已停止</a-select-option>
                        <a-select-option value="error">异常</a-select-option>
                      </a-select>
                      <a-input-search 
                        v-model:value="searchKeyword" 
                        placeholder="搜索 Profile 名称..." 
                        style="width: 240px;"
                        @search="handleSearch"
                        @clear="handleSearch"
                        allow-clear
                      />
                    </a-space>
                  </div>
                </div>
              </template>

              <div v-if="loading" class="loading-container">
                <a-spin size="large" />
              </div>

              <div v-else-if="filteredProfiles.length === 0" class="empty-container">
                <a-empty :description="searchKeyword ? '未找到匹配的 Profile' : '暂无 Profile'">
                </a-empty>
              </div>

              <div v-else class="table-container">
                <a-table 
                  :columns="columns" 
                  :data-source="filteredProfiles"
                  :pagination="false"
                  :row-key="'profile_name'"
                  :custom-row="customRow"
                  @row-click="handleRowClick"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'display_name'">
                      <div class="profile-name-cell">
                        <div class="profile-icon-wrapper">
                          <ApartmentOutlined class="profile-icon" />
                        </div>
                        <div class="profile-info">
                          <div class="profile-display-name">{{ record.display_name }}</div>
                          <div class="profile-name-text">{{ record.profile_name }}</div>
                        </div>
                      </div>
                    </template>

                    <template v-else-if="column.key === 'status'">
                      <span :class="`status-badge status-${record.status}`">
                        <component :is="getStatusIcon(record.status)" class="status-icon" />
                        {{ getStatusText(record.status) }}
                      </span>
                    </template>

                    <template v-else-if="column.key === 'user'">
                      <template v-if="record.user_id">
                        <div class="user-info">
                          <UserOutlined class="user-icon" />
                          <span>{{ record.user_name || '用户 ' + record.user_id }}</span>
                        </div>
                      </template>
                      <template v-else>
                        <span class="no-user">-</span>
                      </template>
                    </template>

                    <template v-else-if="column.key === 'port'">
                      <span v-if="record.port" class="port-text">
                        :{{ record.port }}
                      </span>
                      <span v-else class="no-port">-</span>
                    </template>

                    <template v-else-if="column.key === 'last_activity'">
                      <span class="activity-time">
                        {{ record.last_activity ? formatTime(record.last_activity) : '-' }}
                      </span>
                    </template>

                    <template v-else-if="column.key === 'actions'">
                      <a-space size="small">
                        <a-tooltip v-if="record.status === 'stopped' || record.status === 'error'" title="启动">
                          <a-button 
                            type="text" 
                            size="small"
                            @click.stop="handleStartProfile(record)"
                            :loading="actionLoading[record.profile_name]"
                          >
                            <PlayCircleOutlined />
                          </a-button>
                        </a-tooltip>
                        <a-tooltip v-if="record.status === 'running'" title="停止">
                          <a-button 
                            type="text" 
                            size="small"
                            @click.stop="handleStopProfile(record)"
                            :loading="actionLoading[record.profile_name]"
                          >
                            <PauseCircleOutlined />
                          </a-button>
                        </a-tooltip>
                        <a-tooltip v-if="record.status === 'running'" title="重启">
                          <a-button 
                            type="text" 
                            size="small"
                            @click.stop="handleRestartProfile(record)"
                            :loading="actionLoading[record.profile_name]"
                          >
                            <ReloadOutlined />
                          </a-button>
                        </a-tooltip>
                        <a-tooltip title="查看详情">
                          <a-button 
                            type="text" 
                            size="small"
                            @click.stop="handleViewDetail(record)"
                          >
                            <EyeOutlined />
                          </a-button>
                        </a-tooltip>
                      </a-space>
                    </template>
                  </template>
                </a-table>
              </div>
            </a-card>
          </div>

          <div 
            v-if="selectedProfile" 
            class="detail-panel"
            :class="{ 'panel-open': detailPanelOpen }"
          >
            <div class="panel-header">
              <div class="panel-title">
                <ApartmentOutlined class="panel-icon" />
                <span>Profile 详情</span>
              </div>
              <a-button type="text" class="close-btn" @click="closeDetailPanel">
                <CloseOutlined />
              </a-button>
            </div>

            <div class="panel-content" v-if="detailLoading">
              <a-spin size="large" />
            </div>

            <div v-else-if="profileDetail" class="panel-body">
              <div class="detail-section">
                <div class="section-title">
                  <InfoCircleOutlined class="section-icon" />
                  基本信息
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">显示名称</div>
                    <div class="info-value">{{ profileDetail.display_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Profile 名称</div>
                    <div class="info-value code-value">{{ profileDetail.profile_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">运行状态</div>
                    <div class="info-value">
                      <span :class="`status-badge status-${profileDetail.status}`">
                        <component :is="getStatusIcon(profileDetail.status)" class="status-icon" />
                        {{ getStatusText(profileDetail.status) }}
                      </span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">端口</div>
                    <div class="info-value">
                      <span v-if="profileDetail.port" class="port-text">:{{ profileDetail.port }}</span>
                      <span v-else>-</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">API URL</div>
                    <div class="info-value">
                      <a-tag v-if="profileDetail.api_url" color="blue">
                        {{ profileDetail.api_url }}
                      </a-tag>
                      <span v-else>-</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">是否默认</div>
                    <div class="info-value">
                      <a-tag v-if="profileDetail.is_default" color="green">是</a-tag>
                      <a-tag v-else color="default">否</a-tag>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">会话数</div>
                    <div class="info-value">{{ profileDetail.session_count }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">创建时间</div>
                    <div class="info-value">
                      {{ profileDetail.created_at ? formatTime(profileDetail.created_at) : '-' }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">最后活动</div>
                    <div class="info-value">
                      {{ profileDetail.last_activity ? formatTime(profileDetail.last_activity) : '-' }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">配置路径</div>
                    <div class="info-value code-value">
                      {{ profileDetail.config_path || '-' }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="detail-section">
                <div class="section-title">
                  <TeamOutlined class="section-icon" />
                  关联用户
                </div>
                <div class="user-section">
                  <div v-if="profileDetail.user_id" class="assigned-user">
                    <UserOutlined class="user-avatar" />
                    <div class="user-info-detail">
                      <div class="user-name">{{ profileDetail.user_name || '用户 ' + profileDetail.user_id }}</div>
                      <div class="user-id">ID: {{ profileDetail.user_id }}</div>
                    </div>
                  </div>
                  <div v-else class="no-user-assigned">
                    <UserOutlined class="empty-user-icon" />
                    <span>未关联任何用户</span>
                  </div>
                </div>
              </div>

              <div class="detail-section">
                <div class="section-title">
                  <ToolOutlined class="section-icon" />
                  已安装技能
                  <a-tag color="blue" class="skill-count">
                    {{ profileDetail.skill_count }} 个
                  </a-tag>
                </div>
                <div class="skills-section">
                  <div v-if="profileDetail.skills?.length > 0" class="skills-list">
                    <div 
                      v-for="skill in profileDetail.skills" 
                      :key="skill.name"
                      class="skill-item"
                    >
                      <ToolOutlined class="skill-icon" />
                      <div class="skill-info">
                        <div class="skill-name">{{ skill.display_name || skill.name }}</div>
                        <div class="skill-path">{{ skill.path }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="no-skills">
                    <ToolOutlined class="empty-skill-icon" />
                    <span>暂无已安装技能</span>
                  </div>
                </div>
              </div>

              <div class="detail-section" v-if="profileDetail.config_raw">
                <div class="section-title">
                  <SettingOutlined class="section-icon" />
                  配置内容
                </div>
                <div class="config-section">
                  <div class="config-content">
                    <pre><code>{{ profileDetail.config_raw }}</code></pre>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-actions">
              <a-space>
                <a-button 
                  v-if="profileDetail?.status === 'stopped' || profileDetail?.status === 'error'"
                  type="primary"
                  @click="handleStartProfile(selectedProfile!)"
                  :loading="actionLoading[selectedProfile?.profile_name || '']"
                >
                  <PlayCircleOutlined /> 启动
                </a-button>
                <a-button 
                  v-if="profileDetail?.status === 'running'"
                  @click="handleStopProfile(selectedProfile!)"
                  :loading="actionLoading[selectedProfile?.profile_name || '']"
                >
                  <PauseCircleOutlined /> 停止
                </a-button>
                <a-button 
                  v-if="profileDetail?.status === 'running'"
                  @click="handleRestartProfile(selectedProfile!)"
                  :loading="actionLoading[selectedProfile?.profile_name || '']"
                >
                  <ReloadOutlined /> 重启
                </a-button>
              </a-space>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  ApartmentOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  EyeOutlined,
  CloseOutlined,
  InfoCircleOutlined,
  TeamOutlined,
  ToolOutlined,
  SettingOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import type { 
  ProfileListItem,
  ProfileListResponse,
  ProfileDetail,
  ProfileStatus,
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

const loading = ref(false)
const detailLoading = ref(false)
const actionLoading = ref<Record<string, boolean>>({})

const profileListData = ref<ProfileListResponse | null>(null)
const searchKeyword = ref('')
const filterStatus = ref<string | undefined>(undefined)
const selectedProfile = ref<ProfileListItem | null>(null)
const profileDetail = ref<ProfileDetail | null>(null)
const detailPanelOpen = ref(false)

const columns = [
  { title: '名称', dataIndex: 'display_name', key: 'display_name', width: '25%' },
  { title: '状态', dataIndex: 'status', key: 'status', width: '12%' },
  { title: '关联用户', dataIndex: 'user', key: 'user', width: '15%' },
  { title: '端口', dataIndex: 'port', key: 'port', width: '10%' },
  { title: '最后活动', dataIndex: 'last_activity', key: 'last_activity', width: '18%' },
  { title: '操作', dataIndex: 'actions', key: 'actions', width: '20%', fixed: 'right' },
]

const profileStats = computed(() => ({
  total: profileListData.value?.total || 0,
  running: profileListData.value?.running_count || 0,
  stopped: profileListData.value?.stopped_count || 0,
  error: profileListData.value?.error_count || 0,
}))

const filteredProfiles = computed<ProfileListItem[]>(() => {
  if (!profileListData.value?.items) return []
  
  let profiles = [...profileListData.value.items]
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    profiles = profiles.filter(p => 
      p.profile_name.toLowerCase().includes(keyword) ||
      (p.display_name && p.display_name.toLowerCase().includes(keyword))
    )
  }
  
  if (filterStatus.value) {
    profiles = profiles.filter(p => p.status === filterStatus.value)
  }
  
  profiles.sort((a, b) => {
    const statusOrder: Record<string, number> = {
      running: 0,
      starting: 1,
      stopped: 2,
      error: 3,
    }
    const aOrder = statusOrder[a.status] ?? 4
    const bOrder = statusOrder[b.status] ?? 4
    if (aOrder !== bOrder) return aOrder - bOrder
    
    return (a.profile_name || '').localeCompare(b.profile_name || '')
  })
  
  return profiles
})

const customRow = (record: ProfileListItem) => {
  return {
    onClick: () => handleViewDetail(record),
    style: { cursor: 'pointer' },
  }
}

const getStatusIcon = (status: ProfileStatus) => {
  const icons: Record<string, any> = {
    running: CheckCircleOutlined,
    starting: ReloadOutlined,
    stopped: PauseCircleOutlined,
    error: ExclamationCircleOutlined,
  }
  return icons[status] || PauseCircleOutlined
}

const getStatusText = (status: ProfileStatus) => {
  const texts: Record<string, string> = {
    running: '运行中',
    starting: '启动中',
    stopped: '已停止',
    error: '异常',
  }
  return texts[status] || '未知'
}

const formatTime = (timeStr: string) => {
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timeStr
  }
}

const fetchProfiles = async () => {
  loading.value = true
  try {
    const res = await hermesApi.getProfiles({
      search: searchKeyword.value || undefined,
      status: filterStatus.value,
    })
    if (res.code === 200) {
      profileListData.value = res.data
    } else {
      message.error(res.message || '获取 Profile 列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch profiles:', error)
    message.error('获取 Profile 列表失败')
  } finally {
    loading.value = false
  }
}

const fetchProfileDetail = async (profileName: string) => {
  detailLoading.value = true
  try {
    const res = await hermesApi.getProfileDetail(profileName)
    if (res.code === 200) {
      profileDetail.value = res.data.profile
    } else {
      message.error(res.message || '获取 Profile 详情失败')
    }
  } catch (error) {
    console.error('Failed to fetch profile detail:', error)
    message.error('获取 Profile 详情失败')
  } finally {
    detailLoading.value = false
  }
}

const handleRefresh = () => {
  fetchProfiles()
  if (selectedProfile.value) {
    fetchProfileDetail(selectedProfile.value.profile_name)
  }
}

const handleSearch = () => {
  fetchProfiles()
}

const handleFilterChange = () => {
  fetchProfiles()
}

const handleRowClick = () => {
}

const handleViewDetail = (profile: ProfileListItem) => {
  selectedProfile.value = profile
  detailPanelOpen.value = true
  fetchProfileDetail(profile.profile_name)
}

const closeDetailPanel = () => {
  detailPanelOpen.value = false
  selectedProfile.value = null
  profileDetail.value = null
}

const handleStartProfile = async (profile: ProfileListItem) => {
  Modal.confirm({
    title: '确认启动',
    content: `确定要启动 Profile "${profile.display_name || profile.profile_name}" 吗？`,
    okText: '启动',
    okType: 'primary',
    cancelText: '取消',
    async onOk() {
      actionLoading.value[profile.profile_name] = true
      try {
        const res = await hermesApi.startProfile(profile.profile_name)
        if (res.code === 200) {
          message.success(`Profile "${profile.display_name || profile.profile_name}" 已启动`)
          await fetchProfiles()
          if (selectedProfile.value?.profile_name === profile.profile_name) {
            await fetchProfileDetail(profile.profile_name)
          }
        } else {
          message.error(res.message || '启动失败')
        }
      } catch (error) {
        console.error('Failed to start profile:', error)
        message.error('启动 Profile 失败')
      } finally {
        actionLoading.value[profile.profile_name] = false
      }
    },
  })
}

const handleStopProfile = async (profile: ProfileListItem) => {
  Modal.confirm({
    title: '确认停止',
    content: `确定要停止 Profile "${profile.display_name || profile.profile_name}" 吗？停止后将无法使用。`,
    okText: '停止',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      actionLoading.value[profile.profile_name] = true
      try {
        const res = await hermesApi.stopProfile(profile.profile_name)
        if (res.code === 200) {
          message.success(`Profile "${profile.display_name || profile.profile_name}" 已停止`)
          await fetchProfiles()
          if (selectedProfile.value?.profile_name === profile.profile_name) {
            await fetchProfileDetail(profile.profile_name)
          }
        } else {
          message.error(res.message || '停止失败')
        }
      } catch (error) {
        console.error('Failed to stop profile:', error)
        message.error('停止 Profile 失败')
      } finally {
        actionLoading.value[profile.profile_name] = false
      }
    },
  })
}

const handleRestartProfile = async (profile: ProfileListItem) => {
  Modal.confirm({
    title: '确认重启',
    content: `确定要重启 Profile "${profile.display_name || profile.profile_name}" 吗？`,
    okText: '重启',
    okType: 'primary',
    cancelText: '取消',
    async onOk() {
      actionLoading.value[profile.profile_name] = true
      try {
        const res = await hermesApi.restartProfile(profile.profile_name)
        if (res.code === 200) {
          message.success(`Profile "${profile.display_name || profile.profile_name}" 已重启`)
          await fetchProfiles()
          if (selectedProfile.value?.profile_name === profile.profile_name) {
            await fetchProfileDetail(profile.profile_name)
          }
        } else {
          message.error(res.message || '重启失败')
        }
      } catch (error) {
        console.error('Failed to restart profile:', error)
        message.error('重启 Profile 失败')
      } finally {
        actionLoading.value[profile.profile_name] = false
      }
    },
  })
}

onMounted(() => {
  fetchProfiles()
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
  gap: 16px;
  align-items: center;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-layout {
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 200px);
}

.main-area {
  flex: 1;
  min-width: 0;
  transition: flex 0.3s ease;
}

.main-area:has(+ .panel-open) {
  flex: 0.6;
}

.content-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 18px;
  color: #165DFF;
}

.profile-stats {
  font-size: 13px;
  color: #86909c;
  font-weight: normal;
  margin-left: 8px;
}

.stat-total {
  color: #86909c;
}

.card-title-right {
  display: flex;
  align-items: center;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.table-container {
  margin: 0 -16px;
}

.profile-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-icon {
  font-size: 20px;
  color: #165DFF;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.profile-display-name {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.profile-name-text {
  font-size: 12px;
  color: #86909c;
  font-family: 'Monaco', 'Menlo', monospace;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-icon {
  font-size: 12px;
}

.status-running {
  background: #e6ffed;
  color: #00b42a;
}

.status-starting {
  background: #e6f7ff;
  color: #165DFF;
}

.status-stopped {
  background: #f2f3f5;
  color: #86909c;
}

.status-error {
  background: #fff2f0;
  color: #f53f3f;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #1d2129;
}

.user-icon {
  font-size: 12px;
  color: #165DFF;
}

.no-user {
  color: #c9cdd4;
}

.port-text {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #4e5969;
}

.no-port {
  color: #c9cdd4;
}

.activity-time {
  font-size: 12px;
  color: #86909c;
}

.detail-panel {
  width: 0;
  opacity: 0;
  overflow: hidden;
  transition: all 0.3s ease;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e6eb;
}

.detail-panel.panel-open {
  width: 400px;
  min-width: 400px;
  opacity: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f2f3f5;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.panel-icon {
  font-size: 18px;
  color: #165DFF;
}

.close-btn {
  padding: 4px;
  color: #86909c;
}

.close-btn:hover {
  color: #1d2129;
}

.panel-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.panel-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(100vh - 250px);
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f2f3f5;
}

.section-icon {
  font-size: 14px;
  color: #165DFF;
}

.skill-count {
  margin-left: 8px;
  font-size: 12px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.info-label {
  font-size: 13px;
  color: #86909c;
  flex-shrink: 0;
  width: 80px;
}

.info-value {
  font-size: 13px;
  color: #1d2129;
  flex: 1;
  text-align: right;
  word-break: break-word;
}

.code-value {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #722ed1;
}

.user-section {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.assigned-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #165DFF;
}

.user-info-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.user-id {
  font-size: 12px;
  color: #86909c;
}

.no-user-assigned {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #86909c;
  font-size: 13px;
}

.empty-user-icon {
  font-size: 16px;
  color: #c9cdd4;
}

.skills-section {
  max-height: 200px;
  overflow-y: auto;
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  transition: all 0.2s;
}

.skill-item:hover {
  background: #e8f3ff;
}

.skill-icon {
  font-size: 14px;
  color: #165DFF;
}

.skill-info {
  flex: 1;
  min-width: 0;
}

.skill-name {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-path {
  font-size: 11px;
  color: #86909c;
  font-family: 'Monaco', 'Menlo', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-skills {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #86909c;
  font-size: 13px;
}

.empty-skill-icon {
  font-size: 16px;
  color: #c9cdd4;
}

.config-section {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.config-content {
  max-height: 300px;
  overflow: auto;
  padding: 16px;
}

.config-content pre {
  margin: 0;
  padding: 0;
}

.config-content code {
  color: #d4d4d4;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.panel-actions {
  padding: 16px 20px;
  border-top: 1px solid #f2f3f5;
  background: #fafafa;
}

.panel-actions .ant-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
