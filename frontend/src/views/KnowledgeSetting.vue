<template>
  <MainLayout>
    <div class="knowledge-setting-page">
      <div class="page-header">
        <div class="header-left">
          <SettingOutlined class="page-icon" />
          <div class="header-title">
            <h1>知识库配置</h1>
            <p class="subtitle">配置 AgentNow 知识库系统参数</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-tabs v-model:activeKey="activeTab" class="setting-tabs">
          <a-tab-pane key="storage" tab="存储配置">
            <a-card title="存储配置" class="setting-card">
              <a-descriptions :column="1" bordered>
                <a-descriptions-item label="存储路径">
                  <template v-if="editingKey === 'storage.base_path'">
                    <a-input
                      v-model:value="editValue"
                      placeholder="请输入存储路径"
                      style="width: 400px"
                      @pressEnter="handleSaveConfig('storage.base_path')"
                    />
                    <a-button type="primary" style="margin-left: 8px" @click="handleSaveConfig('storage.base_path')">
                      保存
                    </a-button>
                    <a-button style="margin-left: 8px" @click="handleCancelEdit">
                      取消
                    </a-button>
                  </template>
                  <template v-else>
                    <code class="config-value">{{ getConfigValue('storage.base_path') }}</code>
                    <a-button type="link" size="small" @click="handleStartEdit('storage.base_path')">
                      <EditOutlined /> 编辑
                    </a-button>
                  </template>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="info" show-icon>
                <template #message>
                  <span>存储路径说明</span>
                </template>
                <template #description>
                  <p>知识库文档将存储在此路径下。支持绝对路径和相对路径：</p>
                  <ul class="info-list">
                    <li><strong>绝对路径</strong>: <code>/data/knowledge/docs</code></li>
                    <li><strong>相对路径</strong>: <code>./knowledge_docs</code></li>
                    <li><strong>用户目录</strong>: <code>~/.agentnow/knowledge/docs</code></li>
                  </ul>
                </template>
              </a-alert>
            </a-card>

            <a-card title="存储状态" class="setting-card" style="margin-top: 16px">
              <a-row :gutter="24">
                <a-col :span="6">
                  <a-statistic title="总文档数" :value="storageInfo.total_files" :loading="loadingStorage">
                    <template #suffix>
                      个
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :span="6">
                  <a-statistic title="已使用空间" :value="formatFileSize(storageInfo.total_size)" :loading="loadingStorage" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="可用空间" :value="formatFileSize(storageInfo.free_space)" :loading="loadingStorage" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="存储路径" :value="storageInfo.base_path" :loading="loadingStorage">
                    <template #value>
                      <span class="path-text">{{ storageInfo.base_path || '-' }}</span>
                    </template>
                  </a-statistic>
                </a-col>
              </a-row>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="file" tab="文件配置">
            <a-card title="文件大小限制" class="setting-card">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="单文件最大大小">
                  <template v-if="editingKey === 'file.max_size'">
                    <a-input-number
                      v-model:value="editSizeValue"
                      :min="1"
                      :max="1024"
                      style="width: 120px"
                    />
                    <span style="margin: 0 8px">MB</span>
                    <a-button type="primary" style="margin-left: 8px" @click="handleSaveSizeConfig">
                      保存
                    </a-button>
                    <a-button style="margin-left: 8px" @click="handleCancelEdit">
                      取消
                    </a-button>
                  </template>
                  <template v-else>
                    <span class="config-value">{{ formatFileSizeMB(getConfigValue('file.max_size')) }}</span>
                    <a-button type="link" size="small" @click="handleStartEditSize">
                      <EditOutlined /> 编辑
                    </a-button>
                  </template>
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="warning" show-icon>
                <template #message>
                  <span>大文件提示</span>
                </template>
                <template #description>
                  <p>上传较大的文件可能会导致：</p>
                  <ul class="info-list">
                    <li>上传时间较长</li>
                    <li>占用较多服务器存储空间</li>
                    <li>文档解析和索引时间增加</li>
                  </ul>
                </template>
              </a-alert>
            </a-card>

            <a-card title="允许的文件类型" class="setting-card" style="margin-top: 16px">
              <template #extra>
                <a-button type="link" @click="handleStartEdit('file.allowed_types')">
                  <EditOutlined /> 编辑
                </a-button>
              </template>
              
              <template v-if="editingKey === 'file.allowed_types'">
                <a-textarea
                  v-model:value="editValue"
                  placeholder="请输入允许的文件类型，多个类型用逗号分隔"
                  :rows="3"
                />
                <div style="margin-top: 16px">
                  <a-button type="primary" @click="handleSaveConfig('file.allowed_types')">
                    保存
                  </a-button>
                  <a-button style="margin-left: 8px" @click="handleCancelEdit">
                    取消
                  </a-button>
                </div>
              </template>
              <template v-else>
                <div class="file-types">
                  <a-tag
                    v-for="type in fileTypeList"
                    :key="type"
                    color="blue"
                    style="margin: 4px"
                  >
                    {{ type }}
                  </a-tag>
                </div>
              </template>

              <a-divider />

              <a-alert type="info" show-icon>
                <template #message>
                  <span>支持的文件格式说明</span>
                </template>
                <template #description>
                  <div class="file-format-info">
                    <div class="format-group">
                      <strong>文档格式：</strong>
                      <span class="text-muted">.pdf, .doc, .docx, .txt, .md</span>
                    </div>
                    <div class="format-group">
                      <strong>数据格式：</strong>
                      <span class="text-muted">.json, .csv, .xlsx, .xls</span>
                    </div>
                    <div class="format-group">
                      <strong>演示格式：</strong>
                      <span class="text-muted">.pptx, .ppt</span>
                    </div>
                    <div class="format-group">
                      <strong>网页格式：</strong>
                      <span class="text-muted">.html, .htm, .xml</span>
                    </div>
                  </div>
                </template>
              </a-alert>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="mcp" tab="MCP 服务">
            <a-card title="MCP 服务配置" class="setting-card">
              <a-descriptions :column="1" bordered>
                <a-descriptions-item label="MCP 服务状态">
                  <a-badge :status="mcpEnabled ? 'success' : 'default'" />
                  <span class="status-text">
                    {{ mcpEnabled ? '已启用' : '已禁用' }}
                  </span>
                  <a-switch
                    v-model:checked="mcpEnabled"
                    :loading="savingMcp"
                    style="margin-left: 16px"
                    @change="handleToggleMcp"
                  />
                </a-descriptions-item>
              </a-descriptions>

              <a-divider />

              <a-alert type="info" show-icon>
                <template #message>
                  <span>MCP 服务说明</span>
                </template>
                <template #description>
                  <p>MCP (Model Context Protocol) 服务用于：</p>
                  <ul class="info-list">
                    <li>允许 Hermes 系统调用 AgentNow 的知识库</li>
                    <li>提供标准化的知识库访问接口</li>
                    <li>支持跨系统的知识共享</li>
                  </ul>
                </template>
              </a-alert>
            </a-card>

            <a-card title="知识库统计" class="setting-card" style="margin-top: 16px">
              <a-row :gutter="24">
                <a-col :span="6">
                  <a-statistic title="文档总数" :value="statistics.total_docs" :loading="loadingStats">
                    <template #suffix>
                      篇
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :span="6">
                  <a-statistic title="总大小" :value="formatFileSize(statistics.total_size)" :loading="loadingStats" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="分类数" :value="statistics.total_categories" :loading="loadingStats">
                    <template #suffix>
                      个
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :span="6">
                  <a-statistic title="标签数" :value="statistics.total_tags" :loading="loadingStats">
                    <template #suffix>
                      个
                    </template>
                  </a-statistic>
                </a-col>
              </a-row>

              <a-divider />

              <a-row :gutter="24">
                <a-col :span="12">
                  <a-statistic title="公开文档" :value="statistics.public_docs" :loading="loadingStats">
                    <template #suffix>
                      篇
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :span="12">
                  <a-statistic title="最近7天上传" :value="statistics.recent_uploads" :loading="loadingStats">
                    <template #suffix>
                      篇
                    </template>
                  </a-statistic>
                </a-col>
              </a-row>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="category" tab="分类管理">
            <a-card title="文档分类" class="setting-card">
              <template #extra>
                <a-button type="primary" @click="handleAddCategory" :disabled="!canEditCategory">
                  <PlusOutlined /> 添加分类
                </a-button>
              </template>

              <a-table
                :columns="categoryColumns"
                :data-source="categoryList"
                :loading="loadingCategories"
                row-key="name"
                :pagination="false"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <FolderOutlined class="category-icon" />
                    <span class="category-name">{{ record.name }}</span>
                  </template>
                  <template v-else-if="column.key === 'action'">
                    <a-popconfirm
                      v-if="canEditCategory"
                      title="确定要删除此分类吗？已归类的文档将变为未分类。"
                      ok-text="确定"
                      cancel-text="取消"
                      @confirm="handleDeleteCategory(record.name)"
                    >
                      <a-button type="text" size="small" danger>
                        <DeleteOutlined /> 删除
                      </a-button>
                    </a-popconfirm>
                    <span v-else class="text-muted">无权限</span>
                  </template>
                </template>
              </a-table>

              <a-empty v-if="categoryList.length === 0 && !loadingCategories" description="暂无分类" />
            </a-card>

            <a-modal
              v-model:open="categoryModalVisible"
              title="添加分类"
              @ok="handleCategorySubmit"
              @cancel="handleCategoryCancel"
              :confirmLoading="submittingCategory"
            >
              <a-form
                :model="categoryForm"
                :rules="categoryRules"
                ref="categoryFormRef"
                layout="vertical"
              >
                <a-form-item label="分类名称" name="name">
                  <a-input
                    v-model:value="categoryForm.name"
                    placeholder="请输入分类名称"
                    :disabled="submittingCategory"
                  />
                </a-form-item>
              </a-form>
            </a-modal>
          </a-tab-pane>
        </a-tabs>

        <a-alert type="info" show-icon class="security-alert">
          <template #message>
            <SafetyOutlined /> 配置说明
          </template>
          <template #description>
            <p>此处配置的是 AgentNow 自身的知识库系统参数，与 Hermes 系统的知识库配置相互独立：</p>
            <ul class="info-list">
              <li><strong>AgentNow 知识库</strong>：用于存储企业内部文档，通过文件共享实现知识管理</li>
              <li><strong>Hermes 知识库</strong>：Hermes 系统独立的知识库管理，位于 Hermes 管理菜单下</li>
            </ul>
          </template>
        </a-alert>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, TableColumnsType } from 'ant-design-vue'
import {
  SettingOutlined,
  ReloadOutlined,
  EditOutlined,
  PlusOutlined,
  DeleteOutlined,
  FolderOutlined,
  SafetyOutlined,
} from '@ant-design/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeConfig, FileSystemInfo, StatisticsResponse } from '@/types'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const activeTab = ref('storage')
const loading = ref(false)
const savingMcp = ref(false)
const loadingStorage = ref(false)
const loadingStats = ref(false)
const loadingCategories = ref(false)
const editingKey = ref('')
const editValue = ref('')
const editSizeValue = ref(0)
const submittingCategory = ref(false)
const categoryModalVisible = ref(false)

const configList = ref<KnowledgeConfig[]>([])

const storageInfo = reactive<FileSystemInfo>({
  base_path: '',
  total_files: 0,
  total_size: 0,
  free_space: 0,
})

const statistics = reactive<StatisticsResponse>({
  total_docs: 0,
  total_size: 0,
  total_categories: 0,
  total_tags: 0,
  public_docs: 0,
  recent_uploads: 0,
})

interface CategoryItem {
  name: string
}

const categoryList = ref<CategoryItem[]>([])

const categoryFormRef = ref<FormInstance>()
const categoryForm = reactive({
  name: '',
})

const categoryRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
}

const canEditCategory = computed(() => userStore.hasPermission('knowledge:config:edit'))

const mcpEnabled = computed({
  get: () => {
    const config = configList.value.find(c => c.config_key === 'mcp.enabled')
    return config?.config_value === 'true'
  },
  set: (val) => {
    const config = configList.value.find(c => c.config_key === 'mcp.enabled')
    if (config) {
      config.config_value = val ? 'true' : 'false'
    }
  },
})

const fileTypeList = computed(() => {
  const config = configList.value.find(c => c.config_key === 'file.allowed_types')
  if (!config) return []
  return config.config_value.split(',').map(t => t.trim()).filter(Boolean)
})

const categoryColumns: TableColumnsType = [
  { title: '分类名称', dataIndex: 'name', key: 'name', width: '60%' },
  { title: '操作', key: 'action', width: '40%', align: 'right' },
]

const getConfigValue = (key: string): string => {
  const config = configList.value.find(c => c.config_key === key)
  return config?.config_value || '-'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatFileSizeMB = (value: string): string => {
  const bytes = parseInt(value) || 0
  const mb = bytes / 1024 / 1024
  return `${mb} MB`
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.getConfigs()
    if (res.code === 200) {
      configList.value = res.data
    }
  } catch (error) {
    console.error('Failed to load configs:', error)
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const loadStorageInfo = async () => {
  loadingStorage.value = true
  try {
    const res = await knowledgeApi.getStorageInfo()
    if (res.code === 200) {
      Object.assign(storageInfo, res.data)
    }
  } catch (error) {
    console.error('Failed to load storage info:', error)
  } finally {
    loadingStorage.value = false
  }
}

const loadStatistics = async () => {
  loadingStats.value = true
  try {
    const res = await knowledgeApi.getStatistics()
    if (res.code === 200) {
      Object.assign(statistics, res.data)
    }
  } catch (error) {
    console.error('Failed to load statistics:', error)
  } finally {
    loadingStats.value = false
  }
}

const loadCategories = async () => {
  loadingCategories.value = true
  try {
    const res = await knowledgeApi.getCategories()
    if (res.code === 200) {
      categoryList.value = res.data.categories.map(name => ({ name }))
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  } finally {
    loadingCategories.value = false
  }
}

const handleStartEdit = (key: string) => {
  const config = configList.value.find(c => c.config_key === key)
  if (config) {
    editingKey.value = key
    editValue.value = config.config_value
  }
}

const handleStartEditSize = () => {
  const config = configList.value.find(c => c.config_key === 'file.max_size')
  if (config) {
    editingKey.value = 'file.max_size'
    editSizeValue.value = parseInt(config.config_value) / 1024 / 1024
  }
}

const handleCancelEdit = () => {
  editingKey.value = ''
  editValue.value = ''
  editSizeValue.value = 0
}

const handleSaveConfig = async (key: string) => {
  const config = configList.value.find(c => c.config_key === key)
  if (!config) return

  try {
    const res = await knowledgeApi.updateConfig(config.id, editValue.value)
    if (res.code === 200) {
      message.success('配置已更新')
      config.config_value = editValue.value
      handleCancelEdit()
      loadStorageInfo()
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    message.error('保存配置失败')
  }
}

const handleSaveSizeConfig = async () => {
  const config = configList.value.find(c => c.config_key === 'file.max_size')
  if (!config) return

  const bytes = Math.floor(editSizeValue.value * 1024 * 1024)
  const strValue = String(bytes)

  try {
    const res = await knowledgeApi.updateConfig(config.id, strValue)
    if (res.code === 200) {
      message.success('配置已更新')
      config.config_value = strValue
      handleCancelEdit()
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    message.error('保存配置失败')
  }
}

const handleToggleMcp = async (checked: boolean) => {
  const config = configList.value.find(c => c.config_key === 'mcp.enabled')
  if (!config) return

  savingMcp.value = true
  const strValue = checked ? 'true' : 'false'

  try {
    const res = await knowledgeApi.updateConfig(config.id, strValue)
    if (res.code === 200) {
      message.success(`MCP 服务已${checked ? '启用' : '禁用'}`)
      config.config_value = strValue
    }
  } catch (error) {
    console.error('Failed to update MCP config:', error)
    message.error('操作失败')
    mcpEnabled.value = !checked
  } finally {
    savingMcp.value = false
  }
}

const handleRefresh = () => {
  loadConfigs()
  loadStorageInfo()
  loadStatistics()
  loadCategories()
}

const handleAddCategory = () => {
  categoryForm.name = ''
  categoryModalVisible.value = true
}

const handleCategoryCancel = () => {
  categoryModalVisible.value = false
  categoryFormRef.value?.resetFields()
}

const handleCategorySubmit = async () => {
  try {
    await categoryFormRef.value?.validate()
  } catch {
    return
  }

  submittingCategory.value = true
  try {
    message.info('分类管理功能：目前分类是从已有文档中自动提取的，上传文档时指定分类即可创建新分类')
    categoryModalVisible.value = false
  } catch (error) {
    console.error('Failed to add category:', error)
  } finally {
    submittingCategory.value = false
  }
}

const handleDeleteCategory = async (_name: string) => {
  message.info('分类管理功能：目前分类是从已有文档中自动提取的，删除所有该分类的文档后分类会自动消失')
}

onMounted(() => {
  loadConfigs()
  loadStorageInfo()
  loadStatistics()
  loadCategories()
})
</script>

<style scoped>
.knowledge-setting-page {
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

.setting-tabs {
  padding: 16px 24px;
}

.setting-card {
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

.info-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.info-list li {
  margin: 4px 0;
}

.path-text {
  font-size: 12px;
  color: #86909c;
  word-break: break-all;
}

.file-types {
  display: flex;
  flex-wrap: wrap;
}

.file-format-info {
  margin-top: 8px;
}

.format-group {
  margin: 4px 0;
}

.security-alert {
  margin-top: 24px;
}

.category-icon {
  color: #165DFF;
  margin-right: 8px;
}

.category-name {
  font-weight: 500;
}
</style>
