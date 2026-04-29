<template>
  <MainLayout>
    <div class="knowledge-page">
      <a-card class="page-card">
        <template #title>
          <div class="page-header">
            <span class="page-title">文档列表</span>
            <a-space>
              <a-input-search
                v-model:value="searchKeyword"
                placeholder="搜索文档标题、文件名"
                style="width: 280px"
                @search="handleSearch"
              />
              <a-button type="primary" @click="handleUpload" :disabled="!canCreate">
                <PlusOutlined /> 上传文档
              </a-button>
            </a-space>
          </div>
        </template>

        <div class="filter-bar">
          <a-space :size="16">
            <a-select
              v-model:value="filterCategory"
              placeholder="选择分类"
              allow-clear
              style="width: 150px"
              @change="handleFilter"
            >
              <a-select-option v-for="cat in categories" :key="cat" :value="cat">
                {{ cat }}
              </a-select-option>
            </a-select>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </div>

        <a-table
          :columns="columns"
          :data-source="docList"
          :loading="loading"
          row-key="id"
          :pagination="pagination"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'title'">
              <div class="doc-title">
                <FileOutlined class="doc-icon" />
                <div class="doc-info">
                  <div class="doc-name">{{ record.title }}</div>
                  <div class="doc-filename text-muted">{{ record.file_name }}</div>
                </div>
              </div>
            </template>
            <template v-else-if="column.key === 'file_size'">
              {{ formatFileSize(record.file_size) }}
            </template>
            <template v-else-if="column.key === 'is_public'">
              <a-tag :color="record.is_public ? 'green' : 'orange'">
                {{ record.is_public ? '公开' : '私有' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space size="small">
                <a-button type="link" size="small" @click="handleDownload(record)">
                  下载
                </a-button>
                <a-button
                  v-if="canEdit(record)"
                  type="link"
                  size="small"
                  @click="handleEdit(record)"
                >
                  编辑
                </a-button>
                <a-popconfirm
                  v-if="canDelete(record)"
                  title="确定要删除此文档吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a-button type="link" size="small" danger>
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-modal
        v-model:open="uploadModalVisible"
        title="上传文档"
        :width="720"
        @ok="handleUploadSubmit"
        @cancel="handleUploadCancel"
        :confirmLoading="uploading"
        :closable="!uploading"
        :mask-closable="!uploading"
      >
        <a-form
          :model="uploadForm"
          :rules="uploadRules"
          ref="uploadFormRef"
          layout="vertical"
        >
          <a-row :gutter="24">
            <a-col :span="24">
              <a-form-item label="文档标题" name="title">
                <a-input
                  v-model:value="uploadForm.title"
                  placeholder="请输入文档标题"
                  :disabled="uploading"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="分类" name="category">
                <a-input
                  v-model:value="uploadForm.category"
                  placeholder="请输入分类（可选）"
                  :disabled="uploading"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="是否公开">
                <a-switch
                  v-model:checked="uploadForm.is_public"
                  checked-children="是"
                  un-checked-children="否"
                  :disabled="uploading"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="标签" name="tags">
            <a-select
              v-model:value="uploadForm.tags"
              mode="tags"
              placeholder="请输入标签（可多选）"
              style="width: 100%"
              :disabled="uploading"
            />
          </a-form-item>

          <a-form-item label="描述" name="description">
            <a-textarea
              v-model:value="uploadForm.description"
              placeholder="请输入文档描述（可选）"
              :rows="3"
              :disabled="uploading"
            />
          </a-form-item>

          <a-form-item label="选择文件">
            <a-upload-dragger
              :before-upload="beforeUpload"
              :file-list="fileList"
              :remove="handleRemoveFile"
              :disabled="uploading"
              accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml"
            >
              <p class="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p class="ant-upload-hint">
                支持 PDF、Word、Excel、PPT、TXT、MD、JSON、CSV、HTML、XML 等格式
              </p>
            </a-upload-dragger>
          </a-form-item>

          <a-progress
            v-if="uploading"
            :percent="uploadProgress"
            :stroke-color="uploadProgress === 100 ? '#52c41a' : '#165DFF'"
            :show-info="true"
          />
        </a-form>
      </a-modal>

      <a-modal
        v-model:open="editModalVisible"
        title="编辑文档"
        :width="680"
        @ok="handleEditSubmit"
        @cancel="handleEditCancel"
        :confirmLoading="submitting"
      >
        <a-form
          :model="editForm"
          :rules="editRules"
          ref="editFormRef"
          layout="vertical"
        >
          <a-form-item label="文档标题" name="title">
            <a-input v-model:value="editForm.title" placeholder="请输入文档标题" />
          </a-form-item>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="分类" name="category">
                <a-input v-model:value="editForm.category" placeholder="请输入分类（可选）" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="是否公开">
                <a-switch
                  v-model:checked="editForm.is_public"
                  checked-children="是"
                  un-checked-children="否"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="标签" name="tags">
            <a-select
              v-model:value="editForm.tags"
              mode="tags"
              placeholder="请输入标签（可多选）"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="描述" name="description">
            <a-textarea
              v-model:value="editForm.description"
              placeholder="请输入文档描述（可选）"
              :rows="3"
            />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, TableProps } from 'ant-design-vue'
import {
  PlusOutlined,
  FileOutlined,
  InboxOutlined,
} from '@ant-design/icons-vue'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeDoc, UpdateKnowledgeDocParams } from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { useUserStore } from '@/stores/user'

interface UploadFile {
  uid: string
  name: string
  status: string
  size: number
  originFileObj?: File
}

interface Pagination {
  current: number
  pageSize: number
  total: number
  showSizeChanger: boolean
  showTotal: (total: number) => string
  pageSizeOptions: string[]
}

const userStore = useUserStore()

const canCreate = computed(() => userStore.hasPermission('knowledge:doc:create'))

const loading = ref(false)
const uploading = ref(false)
const submitting = ref(false)
const uploadProgress = ref(0)

const searchKeyword = ref('')
const filterCategory = ref<string | undefined>()

const categories = ref<string[]>([])
const docList = ref<KnowledgeDoc[]>([])

const uploadModalVisible = ref(false)
const editModalVisible = ref(false)
const editId = ref<number | null>(null)

const fileList = ref<UploadFile[]>([])
const selectedFile = ref<File | null>(null)

const uploadFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

const uploadForm = reactive({
  title: '',
  category: '',
  description: '',
  tags: [] as string[],
  is_public: true,
})

const editForm = reactive({
  title: '',
  category: '',
  description: '',
  tags: [] as string[],
  is_public: true,
})

const uploadRules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
}

const editRules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
}

const pagination = reactive<Pagination>({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
  pageSizeOptions: ['10', '20', '50', '100'],
})

const columns = [
  { title: '文档名称', dataIndex: 'title', key: 'title', width: 300 },
  { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 100 },
  { title: '类型', dataIndex: 'file_type', key: 'file_type', width: 100 },
  { title: '公开', dataIndex: 'is_public', key: 'is_public', width: 80 },
  { title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' as const },
]

const canEdit = (record: KnowledgeDoc) => {
  return userStore.hasPermission('knowledge:doc:update') && 
    (userStore.isSuperAdmin || record.created_by === userStore.userInfo?.id)
}

const canDelete = (record: KnowledgeDoc) => {
  return userStore.hasPermission('knowledge:doc:delete') && 
    (userStore.isSuperAdmin || record.created_by === userStore.userInfo?.id)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const fetchDocs = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.getDocs({
      page: pagination.current,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
      category: filterCategory.value,
    })
    if (res.code === 200) {
      docList.value = res.data.items
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const res = await knowledgeApi.getCategories()
    if (res.code === 200) {
      categories.value = res.data
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
  }
}

const beforeUpload = (file: File): boolean => {
  if (fileList.value.length >= 1) {
    message.warning('只能上传一个文件')
    return false
  }
  selectedFile.value = file
  fileList.value = [{
    uid: file.uid || String(Date.now()),
    name: file.name,
    status: 'done',
    size: file.size,
    originFileObj: file,
  }]
  return false
}

const handleRemoveFile = (): boolean => {
  selectedFile.value = null
  fileList.value = []
  return true
}

const resetUploadForm = () => {
  uploadForm.title = ''
  uploadForm.category = ''
  uploadForm.description = ''
  uploadForm.tags = []
  uploadForm.is_public = true
  fileList.value = []
  selectedFile.value = null
  uploadProgress.value = 0
}

const handleUpload = () => {
  resetUploadForm()
  uploadModalVisible.value = true
}

const handleUploadCancel = () => {
  uploadModalVisible.value = false
  uploadFormRef.value?.resetFields()
  resetUploadForm()
}

const handleUploadSubmit = async () => {
  if (!selectedFile.value) {
    message.warning('请选择要上传的文件')
    return
  }

  try {
    await uploadFormRef.value?.validate()
  } catch {
    return
  }

  uploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('title', uploadForm.title)
  if (uploadForm.category) formData.append('category', uploadForm.category)
  if (uploadForm.description) formData.append('description', uploadForm.description)
  if (uploadForm.tags.length > 0) formData.append('tags', JSON.stringify(uploadForm.tags))
  formData.append('is_public', String(uploadForm.is_public))

  try {
    uploadProgress.value = 50
    const res = await knowledgeApi.uploadDoc(formData, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    uploadProgress.value = 100
    
    if (res.code === 200) {
      message.success(res.message || '上传成功')
      uploadModalVisible.value = false
      fetchDocs()
      fetchCategories()
    }
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

const handleEdit = (record: KnowledgeDoc) => {
  editId.value = record.id
  editForm.title = record.title
  editForm.category = record.category || ''
  editForm.description = record.description || ''
  editForm.tags = [...(record.tags || [])]
  editForm.is_public = record.is_public
  editModalVisible.value = true
}

const handleEditCancel = () => {
  editModalVisible.value = false
  editFormRef.value?.resetFields()
}

const handleEditSubmit = async () => {
  if (!editId.value) return

  try {
    await editFormRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const updateParams: UpdateKnowledgeDocParams = {
      title: editForm.title,
      category: editForm.category || undefined,
      description: editForm.description || undefined,
      tags: editForm.tags.length > 0 ? editForm.tags : undefined,
      is_public: editForm.is_public,
    }

    const res = await knowledgeApi.updateDoc(editId.value, updateParams)
    
    if (res.code === 200) {
      message.success('更新成功')
      editModalVisible.value = false
      fetchDocs()
      fetchCategories()
    }
  } catch (error) {
    console.error('更新失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (record: KnowledgeDoc) => {
  try {
    const res = await knowledgeApi.deleteDoc(record.id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchDocs()
    }
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleDownload = async (record: KnowledgeDoc) => {
  try {
    const blob = await knowledgeApi.downloadDoc(record.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = record.file_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('开始下载')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const handleReset = () => {
  searchKeyword.value = ''
  filterCategory.value = undefined
  pagination.current = 1
  fetchDocs()
}

const handleSearch = () => {
  pagination.current = 1
  fetchDocs()
}

const handleFilter = () => {
  pagination.current = 1
  fetchDocs()
}

const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  fetchDocs()
}

onMounted(() => {
  fetchDocs()
  fetchCategories()
})
</script>

<style scoped>
.knowledge-page {
  width: 100%;
}

.page-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.filter-bar {
  margin-bottom: 16px;
}

.doc-title {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.doc-icon {
  font-size: 32px;
  color: #165DFF;
  flex-shrink: 0;
  margin-top: 4px;
}

.doc-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.doc-name {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-filename {
  font-size: 12px;
  color: #86909c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-muted {
  color: #86909c;
}
</style>
