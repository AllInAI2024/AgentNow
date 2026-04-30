<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <SafetyCertificateOutlined class="page-icon" />
          <div class="header-title">
            <h1>操作审计</h1>
            <p class="subtitle">Hermes 管理操作审计日志</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-card :bordered="false" class="filter-card">
          <div class="filter-section">
            <div class="filter-row">
              <div class="filter-item">
                <span class="filter-label">关键词</span>
                <a-input 
                  v-model:value="searchKeyword" 
                  placeholder="搜索操作人、详情..." 
                  style="width: 200px;"
                  allow-clear
                  @pressEnter="handleSearch"
                />
              </div>
              <div class="filter-item">
                <span class="filter-label">操作类型</span>
                <a-select 
                  v-model:value="selectedAction" 
                  placeholder="选择操作类型" 
                  style="width: 180px;"
                  allow-clear
                  @change="handleSearch"
                >
                  <a-select-option 
                    v-for="option in actionTypeOptions" 
                    :key="option.value" 
                    :value="option.value"
                  >
                    {{ option.label }}
                  </a-select-option>
                </a-select>
              </div>
              <div class="filter-item">
                <span class="filter-label">操作人</span>
                <a-input 
                  v-model:value="searchUserName" 
                  placeholder="操作人名称" 
                  style="width: 150px;"
                  allow-clear
                  @pressEnter="handleSearch"
                />
              </div>
              <div class="filter-item">
                <span class="filter-label">时间范围</span>
                <a-range-picker
                  v-model:value="dateRange"
                  :placeholder="['开始日期', '结束日期']"
                  style="width: 240px;"
                  :allow-clear="true"
                  @change="handleDateChange"
                />
              </div>
              <div class="filter-item filter-actions">
                <a-button @click="handleReset">
                  <RedoOutlined /> 重置
                </a-button>
                <a-button type="primary" @click="handleSearch">
                  <SearchOutlined /> 搜索
                </a-button>
              </div>
            </div>
          </div>
        </a-card>

        <a-card :bordered="false" class="content-card">
          <div class="table-stats" v-if="!loading && auditData">
            <span class="stat-text">
              共 <span class="stat-number">{{ auditData.total }}</span> 条记录
            </span>
          </div>

          <div v-if="loading" class="loading-container">
            <a-spin size="large" />
          </div>

          <a-table
            v-else-if="auditData?.items?.length > 0"
            :columns="columns"
            :data-source="auditData.items"
            :pagination="paginationConfig"
            :row-key="'id'"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'timestamp'">
                <div class="time-column">
                  <div class="time-value">{{ formatTime(record.timestamp) }}</div>
                  <div class="time-relative">{{ formatRelativeTime(record.timestamp) }}</div>
                </div>
              </template>

              <template v-else-if="column.key === 'action_name'">
                <a-tag :color="getActionColor(record.action)">
                  {{ record.action_name }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'details'">
                <div class="details-column">
                  <span class="details-text">{{ formatDetails(record) }}</span>
                  <a-button type="link" size="small" @click="handleViewDetail(record)">
                    详情
                  </a-button>
                </div>
              </template>

              <template v-else-if="column.key === 'action'">
                <div class="action-column">
                  <a-button type="link" size="small" @click="handleViewDetail(record)">
                    <EyeOutlined /> 查看
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>

          <div v-else class="empty-container">
            <a-empty :description="searchKeyword || selectedAction || searchUserName || dateRange ? '未找到匹配的审计日志' : '暂无审计日志'">
              <a-button type="primary" @click="handleRefresh">刷新</a-button>
            </a-empty>
          </div>
        </a-card>
      </div>

      <a-modal
        v-model:open="detailModalVisible"
        title="审计日志详情"
        width="700px"
        :footer="null"
      >
        <div v-if="selectedLog" class="detail-content">
          <a-descriptions :column="2" bordered size="middle">
            <a-descriptions-item label="操作ID">
              {{ selectedLog.id }}
            </a-descriptions-item>
            <a-descriptions-item label="操作时间">
              {{ formatDateTime(selectedLog.timestamp) }}
            </a-descriptions-item>
            <a-descriptions-item label="操作人">
              <div class="user-info">
                <UserOutlined class="user-avatar" />
                <span class="user-name">{{ selectedLog.user_name }}</span>
                <span class="user-id">(ID: {{ selectedLog.user_id }})</span>
              </div>
            </a-descriptions-item>
            <a-descriptions-item label="操作类型">
              <a-tag :color="getActionColor(selectedLog.action)">
                {{ selectedLog.action_name }}
              </a-tag>
              <span class="action-code">{{ selectedLog.action }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="目标类型" v-if="selectedLog.target_type">
              {{ selectedLog.target_type }}
            </a-descriptions-item>
            <a-descriptions-item label="目标ID" v-if="selectedLog.target_id">
              {{ selectedLog.target_id }}
            </a-descriptions-item>
            <a-descriptions-item label="IP地址">
              {{ selectedLog.ip_address }}
            </a-descriptions-item>
            <a-descriptions-item label="用户代理">
              {{ selectedLog.user_agent || '-' }}
            </a-descriptions-item>
          </a-descriptions>

          <div class="details-section" v-if="hasDetails(selectedLog.details)">
            <div class="section-title">
              <InfoCircleOutlined class="section-icon" />
              详细信息
            </div>
            <a-card :bordered="false" class="details-card">
              <pre class="details-json">{{ formatJson(selectedLog.details) }}</pre>
            </a-card>
          </div>
        </div>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message, TableColumnsType, TableProps } from 'ant-design-vue'
import {
  SafetyCertificateOutlined,
  ReloadOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  InfoCircleOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import zhCN from 'dayjs/locale/zh-cn'
import type { 
  HermesAuditLog, 
  HermesAuditLogListResponse,
  HermesAuditActionTypeOption,
} from '@/types'
import { HermesActionTypeOptions, HermesActionType } from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

dayjs.extend(relativeTime)
dayjs.locale(zhCN)

const loading = ref(false)
const auditData = ref<HermesAuditLogListResponse | null>(null)

const searchKeyword = ref('')
const selectedAction = ref('')
const searchUserName = ref('')
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

const currentPage = ref(1)
const pageSize = ref(20)

const detailModalVisible = ref(false)
const selectedLog = ref<HermesAuditLog | null>(null)

const actionTypeOptions = computed<HermesAuditActionTypeOption[]>(() => {
  return HermesActionTypeOptions
})

const columns: TableColumnsType = [
  {
    title: '操作时间',
    key: 'timestamp',
    width: 180,
    fixed: 'left',
  },
  {
    title: '操作人',
    key: 'user_name',
    dataIndex: 'user_name',
    width: 120,
  },
  {
    title: '操作类型',
    key: 'action_name',
    width: 140,
  },
  {
    title: '详情',
    key: 'details',
    width: 300,
  },
  {
    title: 'IP地址',
    key: 'ip_address',
    dataIndex: 'ip_address',
    width: 140,
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    fixed: 'right',
  },
]

const paginationConfig = computed<TableProps['pagination']>(() => {
  return {
    current: currentPage.value,
    pageSize: pageSize.value,
    total: auditData.value?.total || 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total) => `共 ${total} 条记录`,
    pageSizeOptions: ['10', '20', '50', '100'],
  }
})

const fetchAuditLogs = async () => {
  loading.value = true
  try {
    let start_time: string | undefined
    let end_time: string | undefined
    
    if (dateRange.value && dateRange.value.length === 2) {
      const startDate = dateRange.value[0]
      const endDate = dateRange.value[1]
      
      start_time = startDate.startOf('day').toISOString()
      end_time = endDate.endOf('day').toISOString()
    }

    const res = await hermesApi.getAuditLogs({
      page: currentPage.value,
      page_size: pageSize.value,
      action: selectedAction.value || undefined,
      user_name: searchUserName.value || undefined,
      start_time,
      end_time,
    })
    
    if (res.code === 200) {
      auditData.value = res.data
    } else {
      message.error(res.message || '获取审计日志失败')
    }
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
    message.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  fetchAuditLogs()
}

const handleSearch = () => {
  currentPage.value = 1
  fetchAuditLogs()
}

const handleReset = () => {
  searchKeyword.value = ''
  selectedAction.value = ''
  searchUserName.value = ''
  dateRange.value = null
  currentPage.value = 1
  fetchAuditLogs()
}

const handleDateChange = () => {
  currentPage.value = 1
}

const handleTableChange = (pagination: any) => {
  currentPage.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchAuditLogs()
}

const handleViewDetail = (record: HermesAuditLog) => {
  selectedLog.value = record
  detailModalVisible.value = true
}

const formatTime = (timestamp: string): string => {
  return dayjs(timestamp).format('HH:mm:ss')
}

const formatDateTime = (timestamp: string): string => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

const formatRelativeTime = (timestamp: string): string => {
  const now = dayjs()
  const time = dayjs(timestamp)
  
  const diffMinutes = now.diff(time, 'minute')
  
  if (diffMinutes < 0) {
    return '刚刚'
  }
  
  const todayStart = now.startOf('day')
  const timeDate = time.startOf('day')
  const diffDays = todayStart.diff(timeDate, 'day')
  
  if (diffDays === 0) {
    if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`
    }
    return '今天 ' + time.format('HH:mm')
  } else if (diffDays === 1) {
    return '昨天 ' + time.format('HH:mm')
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return time.format('MM-DD HH:mm')
  }
}

const formatDetails = (log: HermesAuditLog): string => {
  if (log.target_id) {
    return log.target_id
  }
  if (log.details && typeof log.details === 'object') {
    const keys = Object.keys(log.details)
    if (keys.length > 0) {
      const firstKey = keys[0]
      const value = log.details[firstKey]
      if (typeof value === 'string' || typeof value === 'number') {
        return `${firstKey}: ${value}`
      }
    }
  }
  return '无详情'
}

const hasDetails = (details: Record<string, unknown>): boolean => {
  return details && Object.keys(details).length > 0
}

const formatJson = (obj: Record<string, unknown>): string => {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const getActionColor = (action: string): string => {
  if (action.startsWith('hermes:view')) {
    return 'blue'
  }
  if (action.startsWith('hermes:action')) {
    if (action.includes('delete')) {
      return 'red'
    }
    if (action.includes('export')) {
      return 'green'
    }
    if (action.includes('restart') || action.includes('start') || action.includes('stop')) {
      return 'orange'
    }
    return 'cyan'
  }
  return 'default'
}

watch([currentPage, pageSize], () => {
  fetchAuditLogs()
})

onMounted(() => {
  fetchAuditLogs()
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
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filter-card {
  margin-bottom: 0;
}

.filter-section {
  width: 100%;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #4e5969;
  white-space: nowrap;
}

.filter-actions {
  margin-left: auto;
}

.content-card {
  margin-bottom: 0;
}

.table-stats {
  margin-bottom: 16px;
}

.stat-text {
  font-size: 14px;
  color: #4e5969;
}

.stat-number {
  font-weight: 600;
  color: #1d2129;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.time-column {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-value {
  font-size: 14px;
  color: #1d2129;
}

.time-relative {
  font-size: 12px;
  color: #86909c;
}

.details-column {
  display: flex;
  align-items: center;
  gap: 8px;
}

.details-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #4e5969;
}

.action-column {
  display: flex;
  gap: 8px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  font-size: 20px;
  color: #165DFF;
}

.user-name {
  font-weight: 500;
  color: #1d2129;
}

.user-id {
  font-size: 12px;
  color: #86909c;
}

.action-code {
  font-size: 12px;
  color: #86909c;
  margin-left: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
}

.details-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.section-icon {
  color: #165DFF;
}

.details-card {
  background: #f7f8fa;
  border-radius: 8px;
}

.details-json {
  margin: 0;
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #4e5969;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}
</style>
