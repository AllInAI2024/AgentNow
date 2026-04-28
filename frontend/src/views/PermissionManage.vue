<template>
  <MainLayout>
    <div class="permission-page">
      <a-card class="page-card">
        <template #title>
          <div class="page-header">
            <span class="page-title">功能点管理</span>
            <a-button type="primary" @click="handleAdd">
              <PlusOutlined /> 新增功能点
            </a-button>
          </div>
        </template>

        <a-table
          :columns="columns"
          :data-source="permissionList"
          :loading="loading"
          row-key="id"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <span :style="{ paddingLeft: `${record.level * 24}px` }">
                <FolderOutlined v-if="record.hasChildren" style="margin-right: 8px; color: #165DFF;" />
                <FileOutlined v-else style="margin-right: 8px; color: #86909c;" />
                {{ record.name }}
              </span>
            </template>
            <template v-else-if="column.key === 'type'">
              <a-tag :color="getTypeColor(record.type)">
                {{ getTypeLabel(record.type) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space size="small">
                <a-tooltip title="编辑">
                  <a-button type="text" size="middle" @click="handleEdit(record)">
                    <EditOutlined />
                  </a-button>
                </a-tooltip>
                <a-popconfirm
                  title="确定要删除吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a-tooltip title="删除">
                    <a-button type="text" size="middle" danger>
                      <DeleteOutlined />
                    </a-button>
                  </a-tooltip>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-modal
        v-model:open="modalVisible"
        :title="isEdit ? '编辑功能点' : '新增功能点'"
        :width="680"
        @ok="handleSubmit"
        @cancel="handleCancel"
        :confirmLoading="submitting"
      >
        <a-form
          :model="formData"
          :rules="rules"
          ref="formRef"
          layout="vertical"
        >
          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="上级功能点" name="parent_id">
                <a-tree-select
                  v-model:value="formData.parent_id"
                  :tree-data="parentOptions"
                  :replace-fields="{ children: 'children', title: 'name', key: 'id', value: 'id' }"
                  placeholder="请选择上级功能点（不选则为顶级）"
                  allow-clear
                  :tree-default-expand-all="true"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="功能点名称" name="name">
                <a-input
                  v-model:value="formData.name"
                  placeholder="请输入功能点名称"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="权限编码" name="code">
                <a-input
                  v-model:value="formData.code"
                  placeholder="请输入权限编码，如：user:list"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="类型" name="type">
                <a-select v-model:value="formData.type" placeholder="请选择类型">
                  <a-select-option :value="1">菜单</a-select-option>
                  <a-select-option :value="2">按钮</a-select-option>
                  <a-select-option :value="3">API接口</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="路由路径" name="path">
                <a-input
                  v-model:value="formData.path"
                  placeholder="请输入路由路径或接口路径"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="图标" name="icon">
                <a-input
                  v-model:value="formData.icon"
                  placeholder="请输入图标名称"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import {
  PlusOutlined,
  FolderOutlined,
  FileOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { permissionApi, type Permission, type PermissionTree } from '@/api/permission'
import MainLayout from '@/components/MainLayout.vue'

interface PermissionListItem extends Permission {
  level: number
  hasChildren: boolean
}

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const permissionList = ref<PermissionListItem[]>([])
const permissionTree = ref<PermissionTree[]>([])
const formRef = ref<FormInstance>()

const formData = reactive({
  parent_id: 0,
  name: '',
  code: '',
  type: 1,
  path: '',
  icon: '',
})

const rules = {
  name: [{ required: true, message: '请输入功能点名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入权限编码', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

const columns = [
  { title: '功能点名称', dataIndex: 'name', key: 'name', width: 250 },
  { title: '权限编码', dataIndex: 'code', key: 'code', width: 180 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '路径', dataIndex: 'path', key: 'path', width: 180 },
  { title: '图标', dataIndex: 'icon', key: 'icon', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
]

const parentOptions = computed(() => {
  const options = [...permissionTree.value]
  if (isEdit.value && editId.value) {
    const filterTree = (items: PermissionTree[]): PermissionTree[] => {
      return items
        .filter(item => item.id !== editId.value)
        .map(item => ({
          ...item,
          children: item.children ? filterTree(item.children) : [],
        }))
    }
    return filterTree(options)
  }
  return options
})

const flattenTree = (items: PermissionTree[], level: number = 0): PermissionListItem[] => {
  const result: PermissionListItem[] = []
  items.forEach(item => {
    result.push({
      ...item,
      level,
      hasChildren: item.children && item.children.length > 0,
    })
    if (item.children && item.children.length > 0) {
      result.push(...flattenTree(item.children, level + 1))
    }
  })
  return result
}

const fetchPermissions = async () => {
  loading.value = true
  try {
    const res = await permissionApi.getTree()
    if (res.code === 200) {
      permissionTree.value = res.data
      permissionList.value = flattenTree(res.data)
    }
  } catch (error) {
    console.error('获取权限列表失败:', error)
  } finally {
    loading.value = false
  }
}

const getTypeLabel = (type: number) => {
  const map: Record<number, string> = { 1: '菜单', 2: '按钮', 3: 'API接口' }
  return map[type] || '未知'
}

const getTypeColor = (type: number) => {
  const map: Record<number, string> = { 1: 'blue', 2: 'orange', 3: 'purple' }
  return map[type] || 'default'
}

const resetForm = () => {
  formData.parent_id = 0
  formData.name = ''
  formData.code = ''
  formData.type = 1
  formData.path = ''
  formData.icon = ''
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  modalVisible.value = true
}

const handleEdit = async (record: Permission) => {
  isEdit.value = true
  editId.value = record.id
  loading.value = true
  try {
    const res = await permissionApi.getById(record.id)
    if (res.code === 200) {
      const data = res.data
      formData.parent_id = data.parent_id
      formData.name = data.name
      formData.code = data.code
      formData.type = data.type
      formData.path = data.path || ''
      formData.icon = data.icon || ''
      modalVisible.value = true
    }
  } catch (error) {
    console.error('获取权限详情失败:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (record: Permission) => {
  try {
    const res = await permissionApi.delete(record.id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchPermissions()
    }
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
  resetForm()
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && editId.value) {
      const res = await permissionApi.update(editId.value, { ...formData })
      if (res.code === 200) {
        message.success('更新成功')
        modalVisible.value = false
        fetchPermissions()
      }
    } else {
      const res = await permissionApi.create({
        ...formData,
      })
      if (res.code === 200) {
        message.success('创建成功')
        modalVisible.value = false
        fetchPermissions()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchPermissions()
})
</script>

<style scoped>
.permission-page {
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
</style>