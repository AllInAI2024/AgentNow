<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <SettingOutlined class="page-icon" />
          <div class="header-title">
            <h1>配置管理</h1>
            <p class="subtitle">Hermes 系统配置查看</p>
          </div>
        </div>
        <div class="header-right">
          <a-select
            v-model:value="selectedProfile"
            style="width: 200px"
            :loading="profileLoading"
            @change="handleProfileChange"
          >
            <a-select-option
              v-for="profile in profileList"
              :key="profile.name"
              :value="profile.name"
            >
              <span v-if="profile.is_global">🌐 </span>
              {{ profile.display_name }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-tabs v-model:activeKey="activeTab" class="config-tabs">
          <a-tab-pane key="model" tab="模型配置">
            <a-card title="模型配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="默认模型">
                  <a-tag v-if="config.model.default_model" color="blue">
                    {{ config.model.default_model }}
                  </a-tag>
                  <span v-else class="text-muted">未配置</span>
                </a-descriptions-item>
                <a-descriptions-item label="模型提供商">
                  <a-tag v-if="config.model.model_provider" color="green">
                    {{ config.model.model_provider }}
                  </a-tag>
                  <span v-else class="text-muted">未知</span>
                </a-descriptions-item>
                <a-descriptions-item label="上下文窗口">
                  <template v-if="config.model.context_window">
                    <span class="config-value">{{ formatNumber(config.model.context_window) }} tokens</span>
                  </template>
                  <span v-else class="text-muted">未配置</span>
                </a-descriptions-item>
                <a-descriptions-item label="温度参数">
                  <template v-if="config.model.temperature !== null">
                    <a-progress
                      :percent="config.model.temperature * 100"
                      :show-info="false"
                      :stroke-color="getTemperatureColor(config.model.temperature)"
                      style="width: 120px; display: inline-block; margin-right: 8px;"
                    />
                    <span class="config-value">{{ config.model.temperature }}</span>
                  </template>
                  <span v-else class="text-muted">未配置</span>
                </a-descriptions-item>
                <a-descriptions-item label="最大输出 Tokens">
                  <template v-if="config.model.max_tokens">
                    <span class="config-value">{{ formatNumber(config.model.max_tokens) }}</span>
                  </template>
                  <span v-else class="text-muted">未配置</span>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="terminal" tab="终端配置">
            <a-card title="终端配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="终端后端">
                  <a-tag :color="getBackendColor(config.terminal.backend)">
                    {{ config.terminal.backend || '未配置' }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="工作目录">
                  <span v-if="config.terminal.cwd" class="config-value">{{ config.terminal.cwd }}</span>
                  <span v-else class="text-muted">当前目录</span>
                </a-descriptions-item>
                <a-descriptions-item label="命令超时">
                  <template v-if="config.terminal.timeout">
                    <span class="config-value">{{ config.terminal.timeout }} 秒</span>
                  </template>
                  <span v-else class="text-muted">默认 180 秒</span>
                </a-descriptions-item>
                <a-descriptions-item label="环境变量透传">
                  <template v-if="config.terminal.env_passthrough && config.terminal.env_passthrough.length > 0">
                    <a-tag v-for="env in config.terminal.env_passthrough" :key="env" color="purple" style="margin: 2px;">
                      {{ env }}
                    </a-tag>
                  </template>
                  <span v-else class="text-muted">无</span>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="info" show-icon>
                <template #message>
                  <span>终端后端说明</span>
                </template>
                <template #description>
                  <ul class="backend-list">
                    <li><strong>local</strong>: 直接在本机执行（开发环境）</li>
                    <li><strong>docker</strong>: 在 Docker 容器内执行（安全沙箱）</li>
                    <li><strong>ssh</strong>: 通过 SSH 连接远程服务器</li>
                    <li><strong>modal</strong>: Modal 云沙箱执行</li>
                    <li><strong>daytona</strong>: Daytona 工作区执行</li>
                    <li><strong>singularity</strong>: Singularity/Apptainer 容器执行</li>
                  </ul>
                </template>
              </a-alert>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="api_server" tab="API Server">
            <a-card title="API Server 配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="服务状态">
                  <a-badge :status="config.api_server.enabled ? 'success' : 'default'" />
                  <span class="status-text">
                    {{ config.api_server.enabled ? '已启用' : '已禁用' }}
                  </span>
                </a-descriptions-item>
                <a-descriptions-item label="服务端口">
                  <template v-if="config.api_server.port">
                    <span class="config-value">{{ config.api_server.port }}</span>
                  </template>
                  <span v-else class="text-muted">默认 8642</span>
                </a-descriptions-item>
                <a-descriptions-item label="绑定地址">
                  <span v-if="config.api_server.host" class="config-value">{{ config.api_server.host }}</span>
                  <span v-else class="text-muted">127.0.0.1（仅限本地）</span>
                </a-descriptions-item>
                <a-descriptions-item label="模型名称">
                  <span v-if="config.api_server.model_name" class="config-value">{{ config.api_server.model_name }}</span>
                  <span v-else class="text-muted">{{ selectedProfile === 'global' ? '全局' : selectedProfile }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="CORS 允许来源">
                  <template v-if="config.api_server.cors_origins && config.api_server.cors_origins.length > 0">
                    <div class="cors-origins">
                      <a-tag v-for="origin in config.api_server.cors_origins" :key="origin" color="cyan" style="margin: 2px;">
                        {{ origin }}
                      </a-tag>
                    </div>
                  </template>
                  <span v-else class="text-muted">未配置（仅限同域访问）</span>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="warning" show-icon v-if="!config.api_server.enabled">
                <template #message>
                  <span>API Server 未启用</span>
                </template>
                <template #description>
                  如需使用 HTTP API，需要在 .env 文件中设置 <code>API_SERVER_ENABLED=true</code> 并配置 <code>API_SERVER_KEY</code> 用于认证。
                </template>
              </a-alert>

              <a-alert type="success" show-icon v-if="config.api_server.enabled">
                <template #message>
                  <span>API Server 访问地址</span>
                </template>
                <template #description>
                  <code>http://{{ config.api_server.host || '127.0.0.1' }}:{{ config.api_server.port || 8642 }}</code>
                  <br />
                  <span class="text-muted">认证方式: Bearer Token (API_SERVER_KEY)</span>
                </template>
              </a-alert>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="memory" tab="记忆配置">
            <a-card title="记忆系统配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="自动保存">
                  <a-badge :status="config.memory.auto_save ? 'success' : 'default'" />
                  <span class="status-text">
                    {{ config.memory.auto_save ? '已启用' : '已禁用' }}
                  </span>
                </a-descriptions-item>
                <a-descriptions-item label="MEMORY.md 字符限制">
                  <span class="config-value">{{ formatNumber(config.memory.memory_char_limit) }} 字符</span>
                  <span class="text-muted">（约 {{ Math.round(config.memory.memory_char_limit / 2.75) }} tokens）</span>
                </a-descriptions-item>
                <a-descriptions-item label="USER.md 字符限制">
                  <span class="config-value">{{ formatNumber(config.memory.user_char_limit) }} 字符</span>
                  <span class="text-muted">（约 {{ Math.round(config.memory.user_char_limit / 2.75) }} tokens）</span>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-row :gutter="16">
                <a-col :span="12">
                  <a-card size="small" title="MEMORY.md (Agent 笔记)">
                    <a-progress
                      :percent="67"
                      status="normal"
                      stroke-color="#165DFF"
                    />
                    <p class="memory-info">
                      用于记录环境事实、项目约定、学到的知识等。<br />
                      <span class="text-muted">默认限制: {{ formatNumber(config.memory.memory_char_limit) }} 字符</span>
                    </p>
                  </a-card>
                </a-col>
                <a-col :span="12">
                  <a-card size="small" title="USER.md (用户画像)">
                    <a-progress
                      :percent="35"
                      status="normal"
                      stroke-color="#722ED1"
                    />
                    <p class="memory-info">
                      用于记录用户偏好、沟通风格、期望等。<br />
                      <span class="text-muted">默认限制: {{ formatNumber(config.memory.user_char_limit) }} 字符</span>
                    </p>
                  </a-card>
                </a-col>
              </a-row>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="compression" tab="压缩配置">
            <a-card title="上下文压缩配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="压缩功能">
                  <a-badge :status="config.compression.enabled ? 'success' : 'default'" />
                  <span class="status-text">
                    {{ config.compression.enabled ? '已启用' : '已禁用' }}
                  </span>
                </a-descriptions-item>
                <a-descriptions-item label="压缩策略">
                  <span v-if="config.compression.strategy" class="config-value">{{ config.compression.strategy }}</span>
                  <span v-else class="text-muted">默认策略</span>
                </a-descriptions-item>
                <a-descriptions-item label="压缩阈值">
                  <template v-if="config.compression.threshold_tokens">
                    <span class="config-value">{{ formatNumber(config.compression.threshold_tokens) }} tokens</span>
                  </template>
                  <span v-else class="text-muted">模型默认</span>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="info" show-icon>
                <template #message>
                  <span>上下文压缩说明</span>
                </template>
                <template #description>
                  <p>当对话上下文超出模型上下文窗口限制时，Hermes 会自动压缩历史消息以保持在限制内。压缩过程通常包括：</p>
                  <ul class="compression-list">
                    <li>保留最近的几条消息</li>
                    <li>将较早的消息摘要或合并</li>
                    <li>保留关键的系统提示和工具调用信息</li>
                  </ul>
                </template>
              </a-alert>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="general" tab="通用配置">
            <a-card title="通用配置" class="config-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="日志级别">
                  <a-tag v-if="config.general.log_level" color="orange">
                    {{ config.general.log_level?.toUpperCase() }}
                  </a-tag>
                  <span v-else class="text-muted">默认 (INFO)</span>
                </a-descriptions-item>
                <a-descriptions-item label="自动更新">
                  <a-badge :status="config.general.auto_update ? 'processing' : 'default'" />
                  <span class="status-text">
                    {{ config.general.auto_update ? '已启用' : '已禁用' }}
                  </span>
                </a-descriptions-item>
                <a-descriptions-item label="遥测数据">
                  <a-badge :status="config.general.telemetry_enabled ? 'success' : 'default'" />
                  <span class="status-text">
                    {{ config.general.telemetry_enabled ? '已启用' : '已禁用' }}
                  </span>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-card title="配置文件路径" size="small">
                <a-descriptions :column="1" bordered size="small">
                  <a-descriptions-item label="config.yaml 路径">
                    <code v-if="config.config_file_path">{{ config.config_file_path }}</code>
                    <span v-else class="text-muted">未找到</span>
                  </a-descriptions-item>
                  <a-descriptions-item label=".env 路径">
                    <code v-if="config.env_file_path">{{ config.env_file_path }}</code>
                    <span v-else class="text-muted">未找到</span>
                  </a-descriptions-item>
                  <a-descriptions-item label="最后更新时间">
                    <span v-if="config.last_updated">{{ formatDateTime(config.last_updated) }}</span>
                    <span v-else class="text-muted">未知</span>
                  </a-descriptions-item>
                </a-descriptions>
              </a-card>
            </a-card>
          </a-tab-pane>
        </a-tabs>

        <a-alert type="info" show-icon class="security-alert">
          <template #message>
            <SafetyOutlined /> 安全提示
          </template>
          <template #description>
            所有敏感配置项（API keys、密码、tokens 等）已自动脱敏处理，仅显示部分字符。如需修改配置，请直接编辑 Hermes 的配置文件。
          </template>
        </a-alert>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  SettingOutlined,
  ReloadOutlined,
  SafetyOutlined,
} from '@ant-design/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'
import type {
  ConfigProfileItem,
  ConfigResponse,
} from '@/types'

const activeTab = ref('model')
const loading = ref(false)
const profileLoading = ref(false)
const selectedProfile = ref('global')
const profileList = ref<ConfigProfileItem[]>([])

const defaultConfig: ConfigResponse = {
  profile_name: 'global',
  model: {
    default_model: null,
    model_provider: null,
    context_window: null,
    temperature: null,
    max_tokens: null,
  },
  terminal: {
    backend: null,
    cwd: null,
    timeout: null,
    env_passthrough: [],
  },
  api_server: {
    enabled: false,
    port: null,
    host: null,
    cors_origins: [],
    model_name: null,
  },
  memory: {
    memory_char_limit: 2200,
    user_char_limit: 1375,
    auto_save: true,
  },
  compression: {
    enabled: true,
    strategy: null,
    threshold_tokens: null,
  },
  tools: {
    enabled_tools: [],
    disabled_tools: [],
  },
  general: {
    log_level: null,
    auto_update: false,
    telemetry_enabled: true,
  },
  raw_config: null,
  config_file_path: null,
  env_file_path: null,
  last_updated: null,
}

const config = ref<ConfigResponse>({ ...defaultConfig })

const formatNumber = (num: number | null): string => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const formatDateTime = (dateStr: string | null): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getTemperatureColor = (temp: number | null): string => {
  if (temp === null) return '#165DFF'
  if (temp <= 0.3) return '#10B981'
  if (temp <= 0.7) return '#165DFF'
  return '#F5222D'
}

const getBackendColor = (backend: string | null): string => {
  const colorMap: Record<string, string> = {
    local: 'blue',
    docker: 'cyan',
    ssh: 'purple',
    modal: 'orange',
    daytona: 'green',
    singularity: 'magenta',
  }
  return colorMap[backend || ''] || 'default'
}

const loadProfileList = async () => {
  profileLoading.value = true
  try {
    const response = await hermesApi.getConfigProfiles()
    if (response.code === 200 && response.data) {
      profileList.value = response.data.items
      if (profileList.value.length > 0 && !profileList.value.find(p => p.name === selectedProfile.value)) {
        selectedProfile.value = profileList.value[0].name
      }
    }
  } catch (error) {
      console.error('Failed to load config profiles:', error)
    } finally {
      profileLoading.value = false
    }
}

const loadConfig = async () => {
  loading.value = true
  try {
    let response
    if (selectedProfile.value === 'global') {
      response = await hermesApi.getGlobalConfig()
    } else {
      response = await hermesApi.getProfileConfig(selectedProfile.value)
    }
    
    if (response.code === 200 && response.data) {
      config.value = response.data
    }
  } catch (error) {
    console.error('Failed to load config:', error)
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  loadConfig()
}

const handleProfileChange = () => {
  loadConfig()
}

onMounted(() => {
  loadProfileList()
  loadConfig()
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-content {
  background: #fff;
  border-radius: 8px;
  padding: 0;
}

.config-tabs {
  padding: 16px 24px;
}

.config-card {
  margin-top: 16px;
}

.config-value {
  font-weight: 500;
  color: #1d2129;
}

.text-muted {
  color: #86909c;
}

.status-text {
  margin-left: 8px;
}

.backend-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.backend-list li {
  margin: 4px 0;
}

.cors-origins {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.memory-info {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.compression-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.compression-list li {
  margin: 4px 0;
}

.security-alert {
  margin-top: 24px;
}
</style>