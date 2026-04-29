<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <FileTextOutlined class="page-icon" />
          <div class="header-title">
            <h1>知识库管理</h1>
            <p class="subtitle">RAG 知识库状态与文档管理</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-card class="status-card" v-if="knowledgeStatus">
          <template #title>
            <div class="card-title">
              <InfoCircleOutlined />
              <span>知识库状态</span>
            </div>
          </template>
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="状态">
              <a-tag :color="statusColor">
                <component :is="statusIcon" class="status-icon" />
                {{ statusText }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="总文档数">
              <span class="highlight">{{ knowledgeStatus.total_docs }} 个</span>
            </a-descriptions-item>
            <a-descriptions-item label="总字符数">
              <span class="highlight">{{ formatNumber(knowledgeStatus.total_chars) }} chars</span>
            </a-descriptions-item>
            <a-descriptions-item label="总大小">
              <span>{{ formatBytes(knowledgeStatus.total_size) }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="已索引">
              <span class="highlight-success">{{ knowledgeStatus.indexed_docs }} 个</span>
            </a-descriptions-item>
            <a-descriptions-item label="索引中">
              <span class="highlight-warning">{{ knowledgeStatus.pending_docs }} 个</span>
            </a-descriptions-item>
            <a-descriptions-item label="索引失败">
              <span class="highlight-error">{{ knowledgeStatus.failed_docs }} 个</span>
            </a-descriptions-item>
            <a-descriptions-item label="最后索引时间">
              <span>{{ knowledgeStatus.last_index_at ? formatDateTime(knowledgeStatus.last_index_at) : '-' }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="索引引擎">
              <span>{{ knowledgeStatus.index_engine }}</span>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <a-card class="search-card">
          <a-form layout="inline" :model="searchParams" class="search-form">
            <a-form-item label="关键词">
              <a-input
                v-model:value="searchParams.keyword"
                placeholder="搜索文档名称、内容..."
                style="width: 200px"
                allow-clear
                @change="handleSearch"
              >
                <template #prefix><SearchOutlined /></template>
              </a-input>
            </a-form-item>
            <a-form-item label="文件类型">
              <a-select
                v-model:value="searchParams.file_type"
                placeholder="全部类型"
                style="width: 120px"
                allow-clear
                @change="handleSearch"
              >
                <a-select-option value="md">Markdown (.md)</a-select-option>
                <a-select-option value="txt">文本 (.txt)</a-select-option>
                <a-select-option value="pdf">PDF</a-select-option>
                <a-select-option value="docx">Word</a-select-option>
                <a-select-option value="html">HTML</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="分类">
              <a-select
                v-model:value="searchParams.category"
                placeholder="全部分类"
                style="width: 120px"
                allow-clear
                @change="handleSearch"
              >
                <a-select-option v-for="cat in categories" :key="cat" :value="cat">
                  {{ cat }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="handleSearch" :loading="loading">
                <SearchOutlined /> 搜索
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card>
          <a-table
            :columns="columns"
            :data-source="docList"
            :loading="loading"
            :pagination="paginationConfig"
            row-key="id"
            @change="handleTableChange"
            :scroll="{ x: 800 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'file_name'">
                <div class="file-name-cell">
                  <component :is="getFileIcon(record.file_type)" class="file-icon" />
                  <span class="file-name">{{ record.title || record.file_name }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'file_type'">
                <a-tag v-if="record.file_type" :color="getTypeColor(record.file_type)">
                  {{ record.file_type.toUpperCase() }}
                </a-tag>
                <span v-else>-</span>
              </template>
              <template v-else-if="column.key === 'file_size'">
                {{ formatBytes(record.file_size) }}
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :color="getDocStatusColor(record.status)">
                  {{ getDocStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'updated_at'">
                {{ formatDateTime(record.updated_at) }}
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="viewDetail(record)">
                    详情
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </div>

      <a-modal
        v-model:open="detailModalVisible"
        title="文档详情"
        :width="800"
        :footer="null"
      >
        <a-spin :spinning="detailLoading">
          <a-descriptions :column="2" size="small" bordered v-if="currentDoc">
            <a-descriptions-item label="文件名">
              {{ currentDoc.file_name }}
            </a-descriptions-item>
            <a-descriptions-item label="文件类型">
              <a-tag v-if="currentDoc.file_type" :color="getTypeColor(currentDoc.file_type)">
                {{ currentDoc.file_type.toUpperCase() }}
              </a-tag>
              <span v-else>-</span>
            </a-descriptions-item>
            <a-descriptions-item label="文件大小">
              {{ formatBytes(currentDoc.file_size) }}
            </a-descriptions-item>
            <a-descriptions-item label="字符数">
              {{ formatNumber(currentDoc.char_count) }}
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getDocStatusColor(currentDoc.status)">
                {{ getDocStatusText(currentDoc.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="更新时间">
              {{ formatDateTime(currentDoc.updated_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="标签" v-if="currentDoc.tags && currentDoc.tags.length > 0">
              <a-space>
                <a-tag v-for="tag in currentDoc.tags" :key="tag" color="blue">
                  {{ tag }}
                </a-tag>
              </a-space>
            </a-descriptions-item>
            <a-descriptions-item label="分类" v-if="currentDoc.category">
              {{ currentDoc.category }}
            </a-descriptions-item>
          </a-descriptions>

          <a-tabs v-model:activeKey="activeTab" class="detail-tabs" v-if="currentDoc">
            <a-tab-pane key="content" tab="文档内容">
              <div class="content-preview" v-if="currentDoc.content">
                <pre class="markdown-content">{{ currentDoc.content }}</pre>
              </div>
              <a-empty v-else description="暂无文档内容" />
            </a-tab-pane>
            <a-tab-pane key="outline" tab="文档大纲" v-if="currentDoc.outline && currentDoc.outline.length > 0">
              <a-tree :tree-data="outlineTree" :defaultExpandAll="true" />
            </a-tab-pane>
            <a-tab-pane key="frontmatter" tab="元数据" v-if="currentDoc.frontmatter">
              <a-descriptions :column="1" size="small" bordered>
                <a-descriptions-item v-for="(value, key) in currentDoc.frontmatter" :key="key" :label="key">
                  {{ formatValue(value) }}
                </a-descriptions-item>
              </a-descriptions>
            </a-tab-pane>
          </a-tabs>
        </a-spin>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  FileTextOutlined,
  ReloadOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  FileOutlined,
  FileMarkdownOutlined,
  FileTextOutlined as FileTextIconOutlined,
  FilePdfOutlined,
  FileWordOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'
import type {
  HermesKnowledgeStatus,
  HermesKnowledgeDoc,
  HermesKnowledgeDocDetail,
} from '@/types'

const loading = ref(false)
const detailLoading = ref(false)
const knowledgeStatus = ref<HermesKnowledgeStatus | null>(null)
const docList = ref<HermesKnowledgeDoc[]>([])
const categories = ref<string[]>([])

const searchParams = reactive({
  keyword: '',
  file_type: undefined as string | undefined,
  category: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const paginationConfig = computed<TableProps['pagination']>(() => ({
  current: pagination.current,
  pageSize: pagination.pageSize,
  total: pagination.total,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50', '100'],
}))

const statusColor = computed(() => {
  if (!knowledgeStatus.value) return 'default'
  if (knowledgeStatus.value.status === 'healthy') return 'success'
  if (knowledgeStatus.value.status === 'warning') return 'warning'
  return 'error'
})

const statusText = computed(() => {
  if (!knowledgeStatus.value) return '未知'
  if (knowledgeStatus.value.status === 'healthy') return '索引正常'
  if (knowledgeStatus.value.status === 'warning') return '部分故障'
  return '故障'
})

const statusIcon = computed(() => {
  if (!knowledgeStatus.value) return InfoCircleOutlined
  if (knowledgeStatus.value.status === 'healthy') return CheckCircleOutlined
  if (knowledgeStatus.value.status === 'warning') return ExclamationCircleOutlined
  return CloseCircleOutlined
})

const detailModalVisible = ref(false)
const currentDoc = ref<HermesKnowledgeDocDetail | null>(null)
const activeTab = ref('content')

const outlineTree = computed(() => {
  if (!currentDoc.value?.outline) return []
  return currentDoc.value.outline.map((item) => ({
    title: `${'#'.repeat(item.level)} ${item.title}`,
    key: item.line_number,
    children: [],
  }))
})

const columns: TableProps['columns'] = [
  {
    title: '文档名称',
    key: 'file_name',
    dataIndex: 'file_name',
    minWidth: 250,
  },
  {
    title: '类型',
    key: 'file_type',
    dataIndex: 'file_type',
    width: 100,
  },
  {
    title: '大小',
    key: 'file_size',
    dataIndex: 'file_size',
    width: 100,
  },
  {
    title: '状态',
    key: 'status',
    dataIndex: 'status',
    width: 100,
  },
  {
    title: '更新时间',
    key: 'updated_at',
    dataIndex: 'updated_at',
    width: 160,
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
    fixed: 'right',
  },
]

const formatNumber = (num: number): string => {
  if (!num && num !== 0) return '0'
  return num.toLocaleString()
}

const formatBytes = (bytes: number): string => {
  if (!bytes && bytes !== 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(i > 0 ? 2 : 0)} ${units[i]}`
}

const formatDateTime = (isoString: string): string => {
  if (!isoString) return '-'
  try {
    const date = new Date(isoString)
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  } catch {
    return isoString
  }
}

const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const getTypeColor = (type: string | null): string => {
  if (!type) return 'default'
  const colors: Record<string, string> = {
    md: 'blue',
    txt: 'default',
    pdf: 'red',
    docx: 'blue',
    html: 'green',
  }
  return colors[type] || 'default'
}

const getFileIcon = (type: string | null) => {
  if (!type) return FileOutlined
  const icons: Record<string, typeof FileOutlined> = {
    md: FileMarkdownOutlined,
    txt: FileTextIconOutlined,
    pdf: FilePdfOutlined,
    docx: FileWordOutlined,
    html: FileOutlined,
  }
  return icons[type] || FileOutlined
}

const getDocStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    indexed: 'success',
    indexing: 'processing',
    pending: 'warning',
    failed: 'error',
  }
  return colors[status] || 'default'
}

const getDocStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    indexed: '已索引',
    indexing: '索引中',
    pending: '待索引',
    failed: '失败',
  }
  return texts[status] || status
}

const fetchKnowledgeStatus = async () => {
  try {
    const res = await hermesApi.getKnowledgeStatus()
    if (res.code === 200) {
      knowledgeStatus.value = res.data
    } else {
      message.error(res.message || '获取知识库状态失败')
    }
  } catch (error) {
    console.error('Failed to fetch knowledge status:', error)
  }
}

const fetchDocList = async () => {
  loading.value = true
  try {
    const res = await hermesApi.getKnowledgeDocs({
      page: pagination.current,
      page_size: pagination.pageSize,
      keyword: searchParams.keyword || undefined,
      file_type: searchParams.file_type,
      category: searchParams.category,
    })
    if (res.code === 200) {
      docList.value = res.data.items
      pagination.total = res.data.total
      categories.value = res.data.categories
    } else {
      message.error(res.message || '获取文档列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch doc list:', error)
    message.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  pagination.current = 1
  fetchKnowledgeStatus()
  fetchDocList()
}

const handleSearch = () => {
  pagination.current = 1
  fetchDocList()
}

const handleTableChange = (pag: { current: number; pageSize: number }) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchDocList()
}

const viewDetail = async (doc: HermesKnowledgeDoc) => {
  detailModalVisible.value = true
  detailLoading.value = true
  activeTab.value = 'content'
  try {
    const res = await hermesApi.getKnowledgeDocDetail(doc.id)
    if (res.code === 200) {
      currentDoc.value = res.data
    } else {
      message.error(res.message || '获取文档详情失败')
    }
  } catch (error) {
    console.error('Failed to fetch doc detail:', error)
    message.error('获取文档详情失败')
  } finally {
    detailLoading.value = false
  }
}

handleRefresh()
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

.page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-card {
  margin-bottom: 0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title svg {
  color: #165DFF;
}

.status-icon {
  margin-right: 4px;
  vertical-align: middle;
}

.highlight {
  font-weight: 600;
  color: #165DFF;
}

.highlight-success {
  font-weight: 600;
  color: #00B42A;
}

.highlight-warning {
  font-weight: 600;
  color: #FF7D00;
}

.highlight-error {
  font-weight: 600;
  color: #F53F3F;
}

.search-card {
  margin-bottom: 0;
}

.search-form {
  flex-wrap: wrap;
  row-gap: 8px;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 18px;
  color: #86909c;
  flex-shrink: 0;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-tabs {
  margin-top: 16px;
}

.content-preview {
  max-height: 500px;
  overflow: auto;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  background: #f2f3f5;
}

.markdown-content {
  margin: 0;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #1d2129;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
