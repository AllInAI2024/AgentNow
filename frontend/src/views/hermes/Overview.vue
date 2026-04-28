<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <DashboardOutlined class="page-icon" />
          <div class="header-title">
            <h1>系统概览</h1>
            <p class="subtitle">Hermes 系统整体运行状态与关键指标</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-card class="info-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <RobotOutlined class="card-icon" />
              <span>系统信息</span>
            </div>
          </template>
          <template #extra>
            <a-tooltip :title="overviewData?.system_info.has_update ? '有新版本可用' : '当前已是最新版本'">
              <a-tag 
                :color="overviewData?.system_info.has_update ? 'warning' : 'success'"
                class="version-tag"
                @click="handleCheckVersion"
              >
                v{{ overviewData?.system_info.version }}
                <SyncOutlined v-if="overviewData?.system_info.has_update" class="update-icon" />
              </a-tag>
            </a-tooltip>
          </template>
          
          <div class="info-grid">
            <div class="info-item">
              <div class="info-label">当前版本</div>
              <div class="info-value">v{{ overviewData?.system_info.version || 'unknown' }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">运行状态</div>
              <div class="info-value">
                <span :class="`status-badge status-${overviewData?.system_info.status}`">
                  <CheckCircleOutlined v-if="overviewData?.system_info.status === 'healthy'" />
                  <ExclamationCircleOutlined v-else-if="overviewData?.system_info.status === 'warning'" />
                  <CloseCircleOutlined v-else />
                  {{ statusText }}
                </span>
              </div>
            </div>
            <div class="info-item">
              <div class="info-label">运行时长</div>
              <div class="info-value">{{ overviewData?.system_info.uptime || '未知' }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">API Server</div>
              <div class="info-value">端口 {{ overviewData?.system_info.api_server_port || 8642 }}</div>
            </div>
          </div>
          
          <a-divider v-if="overviewData?.system_info.has_update" />
          
          <div v-if="overviewData?.system_info.has_update" class="update-banner">
            <div class="update-info">
              <AlertOutlined class="update-icon-large" />
              <div>
                <div class="update-title">发现新版本: v{{ overviewData?.system_info.latest_version }}</div>
                <div class="update-desc">建议尽快升级以获取最新功能和安全修复</div>
              </div>
            </div>
            <div class="update-actions">
              <a-button type="primary" @click="handleStartUpdate" :loading="updating">
                <CloudUploadOutlined /> 立即升级
              </a-button>
              <a-button @click="handleCheckVersion" :loading="checkingVersion">
                <ReloadOutlined /> 检查更新
              </a-button>
            </div>
          </div>
        </a-card>

        <a-card class="stats-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <BarChartOutlined class="card-icon" />
              <span>统计概览</span>
            </div>
          </template>
          
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon profile-icon">
                <ApartmentOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.total_profiles || 0 }}</div>
                <div class="stat-label">Profile 总数</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon running-icon">
                <PlayCircleOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.running_profiles || 0 }}</div>
                <div class="stat-label">运行中</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon user-icon">
                <TeamOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.total_users || 0 }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon conv-icon">
                <MessageOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.today_conversations || 0 }}</div>
                <div class="stat-label">今日对话</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon skill-icon">
                <ThunderboltOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.total_skills || 0 }}</div>
                <div class="stat-label">技能数</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon mcp-icon">
                <AppstoreOutlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ overviewData?.statistics.total_mcp_services || 0 }}</div>
                <div class="stat-label">MCP 服务</div>
              </div>
            </div>
          </div>
        </a-card>

        <a-card class="health-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <SafetyCertificateOutlined class="card-icon" />
              <span>健康状态</span>
              <span :class="`health-badge health-${overallHealth}`">
                {{ overallHealthText }}
              </span>
            </div>
          </template>
          
          <a-table 
            :columns="healthColumns" 
            :data-source="healthItems" 
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <span :class="`health-status status-${record.status}`">
                  <CheckCircleOutlined v-if="record.status === 'healthy'" class="icon-healthy" />
                  <ExclamationCircleOutlined v-else-if="record.status === 'warning'" class="icon-warning" />
                  <CloseCircleOutlined v-else class="icon-unhealthy" />
                  {{ getStatusText(record.status) }}
                </span>
              </template>
              <template v-else-if="column.key === 'name'">
                <span class="check-name">{{ record.name }}</span>
              </template>
              <template v-else-if="column.key === 'value'">
                <span class="check-value">{{ record.value || '-' }}</span>
              </template>
              <template v-else-if="column.key === 'message'">
                <span class="check-message">{{ record.message }}</span>
              </template>
            </template>
          </a-table>
        </a-card>

        <a-card class="activity-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <ClockCircleOutlined class="card-icon" />
              <span>最近活动</span>
            </div>
          </template>
          
          <a-timeline>
            <a-timeline-item 
              v-for="(activity, index) in overviewData?.recent_activities || []" 
              :key="index"
              :color="getActivityColor(index)"
            >
              <template #dot>
                <component :is="getActivityIcon(index)" class="timeline-icon" />
              </template>
              <div class="activity-item">
                <div class="activity-header">
                  <span class="activity-event">{{ activity.event }}</span>
                  <span class="activity-time">{{ activity.time }}</span>
                </div>
                <div class="activity-user">
                  <UserOutlined /> {{ activity.user_name }}
                </div>
                <div class="activity-details" v-if="activity.details">
                  {{ activity.details }}
                </div>
              </div>
            </a-timeline-item>
            
            <a-timeline-item v-if="!overviewData?.recent_activities?.length" color="gray">
              暂无活动记录
            </a-timeline-item>
          </a-timeline>
        </a-card>
      </div>
    </div>

    <a-modal
      v-model:open="updateModalVisible"
      title="系统升级"
      :closable="!updating"
      :mask-closable="!updating"
      :footer="null"
      width="500px"
    >
      <div class="update-modal-content">
        <a-steps :current="updateStep" direction="vertical" size="small">
          <a-step title="检查更新" :status="updateStep >= 0 ? 'process' : 'wait'" />
          <a-step title="下载新版本" :status="updateStep >= 1 ? 'process' : 'wait'" />
          <a-step title="安装更新" :status="updateStep >= 2 ? 'process' : 'wait'" />
          <a-step title="完成" :status="updateStep >= 3 ? 'finish' : 'wait'" />
        </a-steps>
        
        <div class="update-progress" v-if="updateProgress">
          <a-progress 
            :percent="updateProgress.progress" 
            :status="updateProgress.status === 'failed' ? 'exception' : 'active'"
            :show-info="true"
          />
          <div class="progress-message">
            {{ updateProgress.message }}
          </div>
          <div class="progress-error" v-if="updateProgress.error">
            错误: {{ updateProgress.error }}
          </div>
        </div>
        
        <div class="update-actions-modal" v-if="updateProgress?.status === 'completed' || updateProgress?.status === 'failed'">
          <a-button 
            v-if="updateProgress?.status === 'completed'" 
            type="primary" 
            @click="handleCloseUpdateModal"
          >
            完成
          </a-button>
          <a-button 
            v-else 
            @click="handleRetryUpdate"
          >
            重试
          </a-button>
        </div>
      </div>
    </a-modal>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  DashboardOutlined,
  ReloadOutlined,
  RobotOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  AlertOutlined,
  CloudUploadOutlined,
  BarChartOutlined,
  ApartmentOutlined,
  PlayCircleOutlined,
  TeamOutlined,
  MessageOutlined,
  ThunderboltOutlined,
  AppstoreOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  UserOutlined,
  ToolOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'
import type { 
  HermesOverviewResponse, 
  HealthCheckItem,
  UpdateProgress 
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

const loading = ref(false)
const checkingVersion = ref(false)
const updating = ref(false)
const updateModalVisible = ref(false)
const updateProgress = ref<UpdateProgress | null>(null)
const updateStep = ref(0)

const overviewData = ref<HermesOverviewResponse | null>(null)

const healthColumns = [
  { title: '检查项', dataIndex: 'name', key: 'name', width: '20%' },
  { title: '状态', dataIndex: 'status', key: 'status', width: '15%' },
  { title: '当前值', dataIndex: 'value', key: 'value', width: '25%' },
  { title: '说明', dataIndex: 'message', key: 'message', width: '40%' },
]

const healthItems = computed<HealthCheckItem[]>(() => {
  return overviewData.value?.health_status?.items || []
})

const overallHealth = computed(() => {
  return overviewData.value?.health_status?.overall || 'unhealthy'
})

const overallHealthText = computed(() => {
  const status = overallHealth.value
  if (status === 'healthy') return '健康'
  if (status === 'warning') return '警告'
  return '异常'
})

const statusText = computed(() => {
  const status = overviewData.value?.system_info.status
  if (status === 'healthy') return '运行中'
  if (status === 'warning') return '部分异常'
  return '异常'
})

const getStatusText = (status: string) => {
  if (status === 'healthy') return '正常'
  if (status === 'warning') return '警告'
  return '异常'
}

const getActivityIcon = (index: number) => {
  const icons = [
    MessageOutlined,
    ToolOutlined,
    PlayCircleOutlined,
    ReloadOutlined,
    DatabaseOutlined,
  ]
  return icons[index % icons.length]
}

const getActivityColor = (index: number) => {
  const colors = ['blue', 'green', 'orange', 'purple', 'cyan']
  return colors[index % colors.length]
}

const fetchOverview = async () => {
  loading.value = true
  try {
    const res = await hermesApi.getOverview()
    if (res.code === 200) {
      overviewData.value = res.data
    } else {
      message.error(res.message || '获取系统概览失败')
    }
  } catch (error) {
    console.error('Failed to fetch overview:', error)
    message.error('获取系统概览失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  fetchOverview()
}

const handleCheckVersion = async () => {
  checkingVersion.value = true
  try {
    const res = await hermesApi.checkVersion()
    if (res.code === 200) {
      if (overviewData.value) {
        overviewData.value.system_info.latest_version = res.data.latest_version
        overviewData.value.system_info.has_update = res.data.has_update
      }
      if (res.data.has_update) {
        message.info(`发现新版本: v${res.data.latest_version}`)
      } else {
        message.success('当前已是最新版本')
      }
    }
  } catch (error) {
    message.error('检查版本更新失败')
  } finally {
    checkingVersion.value = false
  }
}

const pollUpdateProgress = async () => {
  const poll = async () => {
    try {
      const res = await hermesApi.getUpdateProgress()
      if (res.code === 200 && res.data) {
        updateProgress.value = res.data
        
        if (res.data.status === 'checking') {
          updateStep.value = 0
        } else if (res.data.status === 'downloading') {
          updateStep.value = 1
        } else if (res.data.status === 'installing') {
          updateStep.value = 2
        } else if (res.data.status === 'completed') {
          updateStep.value = 3
          return
        } else if (res.data.status === 'failed') {
          return
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000))
        await poll()
      }
    } catch (error) {
      console.error('Poll update progress failed:', error)
    }
  }
  
  await poll()
}

const handleStartUpdate = async () => {
  updateModalVisible.value = true
  updateStep.value = 0
  updateProgress.value = {
    status: 'checking',
    progress: 0,
    message: '正在检查更新...',
    error: null
  }
  
  try {
    updating.value = true
    const res = await hermesApi.startUpdate()
    if (res.code === 200) {
      updateProgress.value = res.data
      pollUpdateProgress()
    } else {
      message.error(res.message || '启动升级失败')
      updateModalVisible.value = false
    }
  } catch (error) {
    message.error('启动升级失败')
    updateModalVisible.value = false
  } finally {
    updating.value = false
  }
}

const handleCloseUpdateModal = () => {
  updateModalVisible.value = false
  fetchOverview()
}

const handleRetryUpdate = () => {
  updateStep.value = 0
  handleStartUpdate()
}

onMounted(() => {
  fetchOverview()
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

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 18px;
  color: #165DFF;
}

.info-card {
  margin-bottom: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #86909c;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

.status-healthy {
  background: #e6ffed;
  color: #00b42a;
}

.status-warning {
  background: #fff7e6;
  color: #ff7d00;
}

.status-unhealthy {
  background: #fff2f0;
  color: #f53f3f;
}

.version-tag {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.update-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.update-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-icon-large {
  font-size: 32px;
  color: #ff7d00;
}

.update-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.update-desc {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.update-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.03) 0%, rgba(114, 46, 209, 0.02) 100%);
  border: 1px solid rgba(229, 230, 235, 0.8);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.profile-icon { background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%); color: #165DFF; }
.running-icon { background: linear-gradient(135deg, #e6ffed 0%, #cbf3d6 100%); color: #00b42a; }
.user-icon { background: linear-gradient(135deg, #fff7e6 0%, #ffedd5 100%); color: #ff7d00; }
.conv-icon { background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); color: #722ed1; }
.skill-icon { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #fa8c16; }
.mcp-icon { background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); color: #08979c; }

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
}

.health-badge {
  margin-left: 12px;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.health-healthy { background: #e6ffed; color: #00b42a; }
.health-warning { background: #fff7e6; color: #ff7d00; }
.health-unhealthy { background: #fff2f0; color: #f53f3f; }

.check-name {
  font-weight: 500;
  color: #1d2129;
}

.check-value {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #4e5969;
}

.check-message {
  font-size: 13px;
  color: #86909c;
}

.health-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.icon-healthy { color: #00b42a; }
.icon-warning { color: #ff7d00; }
.icon-unhealthy { color: #f53f3f; }

.activity-item {
  padding: 4px 0;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-event {
  font-weight: 500;
  color: #1d2129;
  font-size: 14px;
}

.activity-time {
  font-size: 12px;
  color: #86909c;
}

.activity-user {
  font-size: 13px;
  color: #4e5969;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.activity-details {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.timeline-icon {
  font-size: 14px;
}

.update-modal-content {
  padding: 16px 0;
}

.update-progress {
  margin-top: 24px;
}

.progress-message {
  margin-top: 12px;
  font-size: 14px;
  color: #4e5969;
}

.progress-error {
  margin-top: 8px;
  font-size: 13px;
  color: #f53f3f;
}

.update-actions-modal {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
