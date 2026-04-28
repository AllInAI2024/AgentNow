<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <ToolOutlined class="page-icon" />
          <div class="header-title">
            <h1>工具集</h1>
            <p class="subtitle">Hermes 内置工具展示与详情</p>
          </div>
        </div>
        <div class="header-right">
          <a-button @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <div class="content-layout">
          <div class="sidebar">
            <a-card :bordered="false" class="sidebar-card">
              <div class="section-title">
                <AppstoreOutlined class="section-icon" />
                工具分类
              </div>
              <div class="category-list">
                <div 
                  :class="['category-item', { active: selectedCategory === '' }]"
                  @click="selectedCategory = ''"
                >
                  <span class="category-icon">🔧</span>
                  <span class="category-name">全部工具</span>
                  <span class="category-count">{{ totalToolsCount }}</span>
                </div>
                <div 
                  v-for="cat in toolList?.categories || []" 
                  :key="cat.name"
                  :class="['category-item', { active: selectedCategory === cat.name }]"
                  @click="selectedCategory = cat.name"
                >
                  <span class="category-icon">{{ cat.icon }}</span>
                  <span class="category-name">{{ cat.display_name }}</span>
                  <span class="category-count">{{ cat.tool_count }}</span>
                </div>
              </div>
            </a-card>

            <a-card :bordered="false" class="sidebar-card">
              <div class="section-title">
                <InfoCircleOutlined class="section-icon" />
                工具统计
              </div>
              <div class="stats-list">
                <div class="stat-item">
                  <span class="stat-label">总工具数</span>
                  <span class="stat-value">{{ totalToolsCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">工具分类</span>
                  <span class="stat-value">{{ toolList?.categories?.length || 0 }}</span>
                </div>
              </div>
            </a-card>
          </div>

          <div class="main-area">
            <a-card :bordered="false" class="content-card">
              <template #title>
                <div class="card-header">
                  <div class="card-title-left">
                    <ThunderboltOutlined class="card-icon" />
                    <span>{{ currentCategoryName }}</span>
                    <span class="tool-stats">
                      (共 <span class="stat-total">{{ currentCategoryTotal }}</span> 个)
                    </span>
                  </div>
                  <div class="card-title-right">
                    <a-input-search 
                      v-model:value="searchKeyword" 
                      placeholder="搜索工具名称、描述..." 
                      style="width: 280px;"
                      allow-clear
                    />
                  </div>
                </div>
              </template>

              <div v-if="loading" class="loading-container">
                <a-spin size="large" />
              </div>

              <div v-else-if="filteredTools.length === 0" class="empty-container">
                <a-empty :description="searchKeyword ? '未找到匹配的工具' : '该分类暂无工具'" />
              </div>

              <div v-else class="tools-container">
                <div 
                  v-for="category in groupedTools" 
                  :key="category.name"
                  class="tool-category-section"
                >
                  <div class="category-header">
                    <span class="category-icon-large">{{ category.icon }}</span>
                    <span class="category-title">{{ category.display_name }}</span>
                    <span class="category-desc">{{ category.description }}</span>
                    <a-tag color="blue">{{ category.tool_count }} 个工具</a-tag>
                  </div>
                  
                  <div class="tools-grid">
                    <div 
                      v-for="tool in category.tools" 
                      :key="tool.name"
                      class="tool-card"
                      @click="handleViewTool(tool)"
                    >
                      <div class="tool-header">
                        <div class="tool-icon-wrapper">
                          <CodeOutlined class="tool-icon" />
                        </div>
                        <div class="tool-title">
                          <div class="tool-name">{{ tool.name }}</div>
                          <div class="tool-display-name">{{ tool.display_name }}</div>
                        </div>
                        <div class="tool-badges">
                          <a-tag color="blue">内置</a-tag>
                        </div>
                      </div>
                      <div class="tool-description">
                        {{ tool.description }}
                      </div>
                      <div class="tool-footer">
                        <div class="tool-params">
                          <span class="param-label">参数:</span>
                          <span class="param-count">{{ tool.parameters.length }} 个</span>
                        </div>
                        <div class="tool-action">
                          <a-button type="text" size="small">
                            <EyeOutlined /> 查看详情
                          </a-button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </a-card>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="detailModalVisible"
      :title="null"
      :footer="null"
      width="900px"
      :closable="true"
      class="tool-detail-modal"
    >
      <div v-if="selectedTool" class="tool-detail-content">
        <div class="detail-header">
          <div class="detail-icon-wrapper">
            <CodeOutlined class="detail-icon" />
          </div>
          <div class="detail-header-info">
            <div class="detail-name">{{ selectedTool.name }}</div>
            <div class="detail-meta">
              <a-tag color="blue">内置工具</a-tag>
              <span class="detail-category">{{ getCategoryDisplay(selectedTool.category) }}</span>
            </div>
          </div>
        </div>

        <a-tabs v-model:activeKey="activeTab" class="detail-tabs">
          <a-tab-pane key="overview" tab="工具概览">
            <div class="tab-content overview-tab">
              <div class="overview-section">
                <div class="overview-item">
                  <div class="overview-label">显示名称</div>
                  <div class="overview-value">{{ selectedTool.display_name }}</div>
                </div>
                <div class="overview-item">
                  <div class="overview-label">所属分类</div>
                  <div class="overview-value">
                    <a-tag>{{ getCategoryDisplay(selectedTool.category) }}</a-tag>
                  </div>
                </div>
                <div class="overview-item">
                  <div class="overview-label">参数数量</div>
                  <div class="overview-value">{{ selectedTool.parameters.length }} 个</div>
                </div>
              </div>
              
              <div class="description-section">
                <div class="section-subtitle">
                  <InfoCircleOutlined /> 功能描述
                </div>
                <div class="description-content">
                  {{ selectedTool.description }}
                </div>
              </div>

              <div v-if="selectedTool.return_description" class="description-section">
                <div class="section-subtitle">
                  <ExportOutlined /> 返回值描述
                </div>
                <div class="description-content">
                  {{ selectedTool.return_description }}
                </div>
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="parameters" tab="参数说明" :disabled="selectedTool.parameters.length === 0">
            <div class="tab-content params-tab">
              <a-table 
                :columns="paramColumns" 
                :data-source="selectedTool.parameters"
                :pagination="false"
                size="small"
                row-key="name"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'required'">
                    <a-tag :color="record.required ? 'red' : 'default'">
                      {{ record.required ? '必填' : '可选' }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'default'">
                    {{ record.default || '-' }}
                  </template>
                </template>
              </a-table>
            </div>
          </a-tab-pane>

          <a-tab-pane key="examples" tab="使用示例" :disabled="selectedTool.examples.length === 0">
            <div class="tab-content examples-tab">
              <div class="examples-list">
                <div v-for="(example, index) in selectedTool.examples" :key="index" class="example-item">
                  <div class="example-number">示例 {{ index + 1 }}</div>
                  <div class="example-code">
                    <pre><code>{{ example }}</code></pre>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="notes" tab="注意事项" :disabled="!selectedTool.notes">
            <div class="tab-content notes-tab">
              <div class="notes-content">
                <ExclamationCircleOutlined class="notes-icon" />
                <div class="notes-text">{{ selectedTool.notes }}</div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ToolOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  CodeOutlined,
  ExportOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue'
import type { 
  BuiltinTool, 
  BuiltinToolListResponse,
  BuiltinToolCategory,
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

const loading = ref(false)
const toolList = ref<BuiltinToolListResponse | null>(null)
const selectedCategory = ref('')
const searchKeyword = ref('')
const selectedTool = ref<BuiltinTool | null>(null)
const detailModalVisible = ref(false)
const activeTab = ref('overview')

const paramColumns = [
  { title: '参数名', dataIndex: 'name', key: 'name', width: 150 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '是否必填', key: 'required', width: 100 },
  { title: '默认值', key: 'default', width: 120 },
]

const totalToolsCount = computed(() => {
  return toolList.value?.total_tools || 0
})

const currentCategoryName = computed(() => {
  if (!selectedCategory.value) return '工具列表'
  const cat = toolList.value?.categories?.find(c => c.name === selectedCategory.value)
  return cat?.display_name || selectedCategory.value
})

const currentCategoryTotal = computed(() => {
  if (!selectedCategory.value) return totalToolsCount.value
  const cat = toolList.value?.categories?.find(c => c.name === selectedCategory.value)
  return cat?.tool_count || 0
})

const filteredTools = computed<BuiltinTool[]>(() => {
  if (!toolList.value?.tools) return []
  
  let tools = [...toolList.value.tools]
  
  if (selectedCategory.value) {
    tools = tools.filter(t => t.category === selectedCategory.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    tools = tools.filter(t => 
      t.name.toLowerCase().includes(keyword) ||
      t.display_name.toLowerCase().includes(keyword) ||
      t.description.toLowerCase().includes(keyword)
    )
  }
  
  return tools
})

const groupedTools = computed<(BuiltinToolCategory & { tools: BuiltinTool[] })[]>(() => {
  if (!toolList.value?.categories || filteredTools.value.length === 0) return []
  
  const groups: Map<string, BuiltinToolCategory & { tools: BuiltinTool[] }> = new Map()
  
  for (const tool of filteredTools.value) {
    if (!groups.has(tool.category)) {
      const cat = toolList.value.categories.find(c => c.name === tool.category)
      if (cat) {
        groups.set(tool.category, { ...cat, tools: [] })
      }
    }
    const group = groups.get(tool.category)
    if (group) {
      group.tools.push(tool)
    }
  }
  
  return Array.from(groups.values())
})

const getCategoryDisplay = (category: string): string => {
  const cat = toolList.value?.categories?.find(c => c.name === category)
  return cat?.display_name || category
}

const fetchTools = async () => {
  loading.value = true
  try {
    const res = await hermesApi.getTools()
    if (res.code === 200) {
      toolList.value = res.data
    } else {
      message.error(res.message || '获取工具列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch tools:', error)
    message.error('获取工具列表失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  fetchTools()
}

const handleViewTool = (tool: BuiltinTool) => {
  selectedTool.value = tool
  detailModalVisible.value = true
  activeTab.value = 'overview'
}

onMounted(() => {
  fetchTools()
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

.content-layout {
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 200px);
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-card {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.section-icon {
  font-size: 16px;
  color: #165DFF;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 8px;
}

.category-item:hover {
  background: #f2f3f5;
}

.category-item.active {
  background: #e8f3ff;
  color: #165DFF;
}

.category-icon {
  font-size: 16px;
}

.category-name {
  flex: 1;
  font-size: 14px;
  color: inherit;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-count {
  font-size: 12px;
  color: #86909c;
  background: #f2f3f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.category-item.active .category-count {
  background: rgba(22, 93, 255, 0.15);
  color: #165DFF;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f2f3f5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.main-area {
  flex: 1;
  min-width: 0;
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

.tool-stats {
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

.tools-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tool-category-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f7f8fa 0%, transparent 100%);
  border-radius: 8px;
}

.category-icon-large {
  font-size: 24px;
}

.category-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.category-desc {
  font-size: 13px;
  color: #86909c;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.tool-card {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e6eb;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.tool-card:hover {
  border-color: #165DFF;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.1);
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-icon {
  font-size: 20px;
  color: #165DFF;
}

.tool-title {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 2px;
}

.tool-display-name {
  font-size: 12px;
  color: #86909c;
}

.tool-badges {
  flex-shrink: 0;
}

.tool-description {
  font-size: 13px;
  color: #4e5969;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tool-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f2f3f5;
}

.tool-params {
  display: flex;
  align-items: center;
  gap: 4px;
}

.param-label {
  font-size: 12px;
  color: #86909c;
}

.param-count {
  font-size: 12px;
  font-weight: 500;
  color: #1d2129;
}

.tool-action {
  display: flex;
  gap: 8px;
}

:deep(.tool-detail-modal .ant-modal-body) {
  padding: 0;
}

.tool-detail-content {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f2f3f5;
}

.detail-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.detail-icon {
  font-size: 28px;
  color: #165DFF;
}

.detail-header-info {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 20px;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 8px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-category {
  font-size: 14px;
  color: #4e5969;
}

.detail-tabs {
  flex: 1;
  overflow: hidden;
}

.tab-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.overview-tab {
  padding: 24px;
}

.overview-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.overview-label {
  font-size: 13px;
  color: #86909c;
}

.overview-value {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.description-section {
  margin-bottom: 24px;
}

.section-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.description-content {
  font-size: 14px;
  color: #4e5969;
  line-height: 1.6;
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.params-tab {
  padding: 16px 24px;
}

.examples-tab {
  padding: 16px 24px;
}

.examples-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.example-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-number {
  font-size: 13px;
  font-weight: 600;
  color: #165DFF;
}

.example-code {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
}

.example-code pre {
  margin: 0;
  padding: 0;
}

.example-code code {
  color: #d4d4d4;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.notes-tab {
  padding: 24px;
}

.notes-content {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
}

.notes-icon {
  font-size: 20px;
  color: #faad14;
  flex-shrink: 0;
}

.notes-text {
  font-size: 14px;
  color: #4e5969;
  line-height: 1.6;
}
</style>
