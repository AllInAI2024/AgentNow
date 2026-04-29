<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <AppstoreOutlined class="page-icon" />
          <div class="header-title">
            <h1>MCP 服务</h1>
            <p class="subtitle">MCP 服务配置与工具列表</p>
          </div>
        </div>
        <div class="header-right">
          <a-button @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <div class="stats-row">
          <a-card :bordered="false" class="stat-card">
            <div class="stat-icon total">
              <AppstoreOutlined />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ mcpList?.total || 0 }}</div>
              <div class="stat-label">MCP 服务总数</div>
            </div>
          </a-card>
          <a-card :bordered="false" class="stat-card">
            <div class="stat-icon running">
              <CheckCircleOutlined />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ mcpList?.running_count || 0 }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </a-card>
          <a-card :bordered="false" class="stat-card">
            <div class="stat-icon warning">
              <ExclamationCircleOutlined />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ mcpList?.warning_count || 0 }}</div>
              <div class="stat-label">警告</div>
            </div>
          </a-card>
          <a-card :bordered="false" class="stat-card">
            <div class="stat-icon stopped">
              <CloseCircleOutlined />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ mcpList?.stopped_count || 0 }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </a-card>
        </div>

        <div class="main-area">
          <a-card :bordered="false" class="content-card">
            <template #title>
              <div class="card-header">
                <div class="card-title-left">
                  <AppstoreOutlined class="card-icon" />
                  <span>MCP 服务列表</span>
                </div>
              </div>
            </template>

            <div v-if="loading" class="loading-container">
              <a-spin size="large" />
            </div>

            <div v-else-if="!mcpList || mcpList.items.length === 0" class="empty-container">
              <a-empty description="暂无 MCP 服务">
                <a-button type="primary" @click="handleRefresh">
                  <ReloadOutlined /> 刷新
                </a-button>
              </a-empty>
            </div>

            <a-table
              v-else
              :columns="columns"
              :data-source="mcpList.items"
              :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: (total: number) => `共 ${total} 个服务` }"
              row-key="name"
              :loading="loading"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'name'">
                  <div class="service-name" @click="handleViewDetail(record)">
                    <AppstoreOutlined class="service-icon" />
                    <span>{{ record.name }}</span>
                  </div>
                </template>
                <template v-else-if="column.key === 'type'">
                  <a-tag :color="record.type === 'stdio' ? 'blue' : 'purple'">
                    <template v-if="record.type === 'stdio'">
                      <DesktopOutlined />
                    </template>
                    <template v-else>
                      <GlobalOutlined />
                    </template>
                    {{ record.type_display }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="getStatusColor(record.status)">
                    <component :is="getStatusIcon(record.status)" />
                    {{ getStatusText(record.status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'tools'">
                  <div class="tool-count">
                    <ToolOutlined class="tool-icon" />
                    <span>{{ record.tool_count }} 个工具</span>
                  </div>
                </template>
                <template v-else-if="column.key === 'last_check'">
                  <span>{{ record.last_check ? formatTime(record.last_check) : '-' }}</span>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <div class="action-buttons">
                    <a-button type="link" size="small" @click.stop="handleViewDetail(record)">
                      <EyeOutlined /> 详情
                    </a-button>
                    <a-button type="link" size="small" @click.stop="handleTestConnection(record)">
                      <PlayCircleOutlined /> 测试
                    </a-button>
                  </div>
                </template>
              </template>
            </a-table>
          </a-card>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="detailModalVisible"
      :title="null"
      :footer="null"
      width="600px"
      :closable="true"
      class="mcp-detail-modal"
    >
      <div v-if="selectedService" class="detail-modal-content">
        <div class="detail-header">
          <div class="detail-icon-wrapper">
            <AppstoreOutlined class="detail-icon" :class="selectedService.status" />
          </div>
          <div class="detail-header-info">
            <div class="detail-name">{{ selectedService.name }}</div>
            <div class="detail-meta">
              <a-tag :color="selectedService.type === 'stdio' ? 'blue' : 'purple'">
                {{ selectedService.type_display }}
              </a-tag>
              <a-tag :color="getStatusColor(selectedService.status)">
                {{ getStatusText(selectedService.status) }}
              </a-tag>
            </div>
          </div>
        </div>

        <a-divider />

        <div class="detail-content">
          <div class="detail-section">
            <div class="section-title">
              <InfoCircleOutlined class="section-icon" />
              基本信息
            </div>
            <div class="info-list">
              <div class="info-item">
                <div class="info-label">服务类型</div>
                <div class="info-value">
                  <component :is="selectedService.type === 'stdio' ? 'DesktopOutlined' : 'GlobalOutlined'" class="info-icon" />
                  {{ selectedService.type_display }}
                </div>
              </div>
              <div class="info-item" v-if="selectedService.command">
                <div class="info-label">启动命令</div>
                <div class="info-value">
                  <code class="command-text">{{ selectedService.command }} {{ selectedService.args?.join(' ') || '' }}</code>
                </div>
              </div>
              <div class="info-item" v-if="selectedService.url">
                <div class="info-label">服务 URL</div>
                <div class="info-value url-value">
                  <LinkOutlined class="link-icon" />
                  <a :href="selectedService.url" target="_blank" rel="noopener noreferrer">
                    {{ selectedService.url }}
                  </a>
                </div>
              </div>
              <div class="info-item">
                <div class="info-label">工具数量</div>
                <div class="info-value">
                  <ToolOutlined class="info-icon" />
                  {{ selectedService.tool_count }} 个工具
                </div>
              </div>
              <div class="info-item" v-if="selectedService.last_check">
                <div class="info-label">最后检查</div>
                <div class="info-value">
                  <ClockCircleOutlined class="info-icon" />
                  {{ formatTime(selectedService.last_check) }}
                </div>
              </div>
              <div class="info-item error-item" v-if="selectedService.error_message">
                <div class="info-label">错误信息</div>
                <div class="info-value error-value">
                  <AlertOutlined class="error-icon" />
                  {{ selectedService.error_message }}
                </div>
              </div>
            </div>
          </div>

          <a-divider />

          <div class="detail-section">
            <div class="section-title">
              <ToolOutlined class="section-icon" />
              提供的工具 ({{ selectedService.tools.length }})
            </div>
            <div v-if="selectedService.tools.length === 0" class="empty-tools">
              <a-empty description="该服务暂无工具" />
            </div>
            <div v-else class="tools-list">
              <a-collapse v-model:activeKey="activeToolKeys">
                <a-collapse-panel
                  v-for="tool in selectedService.tools"
                  :key="tool.name"
                  :header="getToolHeader(tool)"
                >
                  <div class="tool-detail">
                    <div class="tool-desc">{{ tool.description || '暂无描述' }}</div>
                    <div class="tool-schema" v-if="tool.input_schema">
                      <div class="schema-title">输入参数:</div>
                      <pre class="schema-content"><code>{{ JSON.stringify(tool.input_schema, null, 2) }}</code></pre>
                    </div>
                  </div>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </div>

          <a-divider v-if="selectedService.config_raw" />

          <div class="detail-section" v-if="selectedService.config_raw">
            <div class="section-title">
              <SettingOutlined class="section-icon" />
              配置原文
            </div>
            <div class="config-raw">
              <pre><code>{{ selectedService.config_raw }}</code></pre>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <a-button type="primary" @click="handleTestConnection(selectedService)" :loading="testingService">
            <PlayCircleOutlined /> 测试连接
          </a-button>
          <a-button @click="handleCloseDetail">
            <CloseOutlined /> 关闭
          </a-button>
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="testModalVisible"
      title="连接测试结果"
      :footer="null"
      width="600px"
    >
      <div class="test-result-content">
        <div :class="['test-status', testResult?.success ? 'success' : 'error']">
          <component :is="testResult?.success ? 'CheckCircleOutlined' : 'CloseCircleOutlined'" class="status-icon" />
          <div class="status-text">{{ testResult?.message }}</div>
        </div>
        <div v-if="testResult?.tools && testResult.tools.length > 0" class="test-tools">
          <div class="test-tools-title">发现的工具 ({{ testResult.tool_count }})</div>
          <div class="test-tools-list">
            <a-tag v-for="tool in testResult.tools" :key="tool.name" color="blue">
              <ToolOutlined class="tag-icon" />
              {{ tool.name }}
            </a-tag>
          </div>
        </div>
        <div v-if="testResult?.error" class="test-error">
          <div class="test-error-title">错误详情:</div>
          <div class="test-error-message">{{ testResult.error }}</div>
        </div>
      </div>
    </a-modal>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import {
  AppstoreOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  ToolOutlined,
  InfoCircleOutlined,
  DesktopOutlined,
  GlobalOutlined,
  CloseOutlined,
  LinkOutlined,
  ClockCircleOutlined,
  AlertOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import type {
  MCPService,
  MCPServiceListResponse,
  MCPServiceTestResult,
  MCPTool,
  HealthStatus,
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'
import type { TableColumnsType } from 'ant-design-vue'

const loading = ref(false)
const testingService = ref(false)

const mcpList = ref<MCPServiceListResponse | null>(null)
const selectedService = ref<MCPService | null>(null)
const activeToolKeys = ref<string[]>([])

const detailModalVisible = ref(false)
const testModalVisible = ref(false)
const testResult = ref<MCPServiceTestResult | null>(null)

const columns: TableColumnsType = [
  { title: '服务名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 160 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '工具数', dataIndex: 'tools', key: 'tools', width: 120 },
  { title: '最后检查', dataIndex: 'last_check', key: 'last_check', width: 180 },
  { title: '操作', key: 'actions', width: 160, fixed: 'right' },
]

const getStatusColor = (status: HealthStatus): string => {
  switch (status) {
    case 'healthy':
      return 'green'
    case 'warning':
      return 'orange'
    case 'unhealthy':
      return 'red'
    default:
      return 'default'
  }
}

const getStatusIcon = (status: HealthStatus) => {
  switch (status) {
    case 'healthy':
      return CheckCircleOutlined
    case 'warning':
      return ExclamationCircleOutlined
    case 'unhealthy':
      return CloseCircleOutlined
    default:
      return ExclamationCircleOutlined
  }
}

const getStatusText = (status: HealthStatus): string => {
  switch (status) {
    case 'healthy':
      return '运行中'
    case 'warning':
      return '警告'
    case 'unhealthy':
      return '已停止'
    default:
      return '未知'
  }
}

const formatTime = (timeStr: string): string => {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getToolHeader = (tool: MCPTool) => {
  return h('div', { class: 'tool-header' }, [
    h(ToolOutlined, { class: 'tool-header-icon' }),
    h('span', { class: 'tool-header-name' }, tool.name),
    h('span', { class: 'tool-header-desc' }, tool.description || '暂无描述'),
  ])
}

const loadMcpServices = async () => {
  loading.value = true
  try {
    const response = await hermesApi.getMcpServices()
    if (response.code === 200) {
      mcpList.value = response.data
    } else {
      message.error(response.message || '获取 MCP 服务列表失败')
    }
  } catch (error: any) {
    message.error(error.message || '获取 MCP 服务列表失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  loadMcpServices()
}

const handleViewDetail = (service: MCPService) => {
  selectedService.value = service
  if (service.tools.length > 0) {
    activeToolKeys.value = [service.tools[0].name]
  } else {
    activeToolKeys.value = []
  }
  detailModalVisible.value = true
}

const handleCloseDetail = () => {
  detailModalVisible.value = false
  selectedService.value = null
  activeToolKeys.value = []
}

const handleTestConnection = async (service: MCPService) => {
  testingService.value = true
  try {
    const response = await hermesApi.testMcpService(service.name)
    if (response.code === 200) {
      testResult.value = response.data
      testModalVisible.value = true
      if (response.data.success) {
        message.success(response.data.message)
      } else {
        message.warning(response.data.message)
      }
    } else {
      message.error(response.message || '测试连接失败')
    }
  } catch (error: any) {
    message.error(error.message || '测试连接失败')
  } finally {
    testingService.value = false
  }
}

onMounted(() => {
  loadMcpServices()
})
</script>

<style scoped>
.hermes-page {
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px !important;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.total {
  background: rgba(22, 93, 255, 0.1);
  color: #165DFF;
}

.stat-icon.running {
  background: rgba(0, 180, 42, 0.1);
  color: #00B42A;
}

.stat-icon.warning {
  background: rgba(255, 135, 0, 0.1);
  color: #FF8700;
}

.stat-icon.stopped {
  background: rgba(245, 63, 63, 0.1);
  color: #F53F3F;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #86909c;
  margin-top: 4px;
}

.main-area {
  width: 100%;
}

.content-card {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  color: #165DFF;
  font-size: 16px;
}

.loading-container,
.empty-container {
  padding: 60px 0;
  text-align: center;
}

.service-name {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.service-icon {
  color: #165DFF;
}

.service-name:hover {
  color: #165DFF;
}

.tool-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-icon {
  color: #86909c;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.detail-modal-content {
  padding: 0;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.detail-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(22, 93, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-icon {
  font-size: 28px;
  color: #165DFF;
}

.detail-icon.healthy {
  color: #00B42A;
}

.detail-icon.warning {
  color: #FF8700;
}

.detail-icon.unhealthy {
  color: #F53F3F;
}

.detail-header-info {
  flex: 1;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}

.detail-meta {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.detail-content {
  max-height: 500px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 16px;
}

.section-icon {
  color: #165DFF;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  font-size: 14px;
  color: #1d2129;
  display: flex;
  align-items: center;
  gap: 6px;
  word-break: break-all;
}

.info-icon {
  color: #86909c;
}

.command-text {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  word-break: break-all;
}

.url-value {
  display: flex;
  align-items: center;
  gap: 6px;
}

.link-icon {
  color: #165DFF;
}

.url-value a {
  color: #165DFF;
  text-decoration: none;
  word-break: break-all;
}

.url-value a:hover {
  text-decoration: underline;
}

.error-item {
  background: rgba(245, 63, 63, 0.08);
  padding: 12px;
  border-radius: 8px;
}

.error-value {
  color: #F53F3F;
}

.error-icon {
  color: #F53F3F;
}

.empty-tools {
  text-align: center;
  padding: 24px 0;
}

.tools-list {
  max-height: 300px;
  overflow-y: auto;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-header-icon {
  color: #165DFF;
}

.tool-header-name {
  font-weight: 500;
  color: #1d2129;
}

.tool-header-desc {
  flex: 1;
  color: #86909c;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-left: 8px;
}

.tool-detail {
  padding: 8px 0;
}

.tool-desc {
  font-size: 14px;
  color: #4e5969;
  margin-bottom: 12px;
}

.tool-schema {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.schema-title {
  font-size: 13px;
  font-weight: 500;
  color: #86909c;
  margin-bottom: 8px;
}

.schema-content {
  margin: 0;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #1d2129;
  max-height: 200px;
  overflow-y: auto;
}

.config-raw {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.config-raw pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #1d2129;
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.test-result-content {
  padding: 8px 0;
}

.test-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.test-status.success {
  background: rgba(0, 180, 42, 0.08);
}

.test-status.error {
  background: rgba(245, 63, 63, 0.08);
}

.status-icon {
  font-size: 32px;
}

.test-status.success .status-icon {
  color: #00B42A;
}

.test-status.error .status-icon {
  color: #F53F3F;
}

.status-text {
  font-size: 16px;
  font-weight: 500;
}

.test-status.success .status-text {
  color: #00B42A;
}

.test-status.error .status-text {
  color: #F53F3F;
}

.test-tools {
  margin-bottom: 20px;
}

.test-tools-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  margin-bottom: 12px;
}

.test-tools-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.test-tools-list .ant-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-icon {
  font-size: 12px;
}

.test-error {
  background: rgba(245, 63, 63, 0.08);
  padding: 12px;
  border-radius: 8px;
}

.test-error-title {
  font-size: 13px;
  font-weight: 500;
  color: #F53F3F;
  margin-bottom: 8px;
}

.test-error-message {
  font-size: 14px;
  color: #F53F3F;
  word-break: break-all;
}
</style>
