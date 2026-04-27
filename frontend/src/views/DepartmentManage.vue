<template>
  <MainLayout>
    <div class="department-page">
      <a-card class="page-card">
        <template #title>
          <div class="page-header">
            <span class="page-title">部门管理</span>
            <a-button type="primary" @click="handleAdd">
              <PlusOutlined /> 新增部门
            </a-button>
          </div>
        </template>

        <a-table
          :columns="columns"
          :data-source="departmentList"
          :loading="loading"
          row-key="id"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <span :style="{ paddingLeft: `${record.level * 24}px` }">
                <ApartmentOutlined v-if="record.hasChildren" style="margin-right: 8px; color: #165DFF;" />
                <TeamOutlined v-else style="margin-right: 8px; color: #86909c;" />
                {{ record.name }}
              </span>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.status === 1 ? 'green' : 'red'">
                {{ record.status === 1 ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="handleEdit(record)">
                  编辑
                </a-button>
                <a-popconfirm
                  title="确定要删除吗？删除后子部门和该部门下的员工也会被删除。"
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
        v-model:open="modalVisible"
        :title="isEdit ? '编辑部门' : '新增部门'"
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
              <a-form-item label="上级部门" name="parent_id">
                <a-tree-select
                  v-model:value="formData.parent_id"
                  :tree-data="parentOptions"
                  :replace-fields="{ children: 'children', title: 'name', key: 'id', value: 'id' }"
                  placeholder="请选择上级部门（不选则为顶级部门）"
                  allow-clear
                  :tree-default-expand-all="true"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="部门名称" name="name">
                <a-input
                  v-model:value="formData.name"
                  placeholder="请输入部门名称"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="部门编码" name="code">
                <a-input
                  v-model:value="formData.code"
                  placeholder="请输入部门编码"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="状态" name="status">
                <a-select v-model:value="formData.status" placeholder="请选择状态">
                  <a-select-option :value="1">启用</a-select-option>
                  <a-select-option :value="0">禁用</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="排序" name="sort">
                <a-input-number
                  v-model:value="formData.sort"
                  placeholder="数字越小越靠前"
                  :min="0"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="部门负责人" name="leader_id">
                <a-select
                  v-model:value="formData.leader_id"
                  placeholder="请选择部门负责人（可选）"
                  allow-clear
                  :options="employeeOptions"
                  :field-names="{ label: 'username', value: 'id' }"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="部门描述" name="description">
            <a-textarea
              v-model:value="formData.description"
              placeholder="请输入部门描述"
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
import type { FormInstance } from 'ant-design-vue'
import {
  PlusOutlined,
  ApartmentOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import { departmentApi } from '@/api/department'
import { employeeApi } from '@/api/employee'
import type { Department, DepartmentTree, User } from '@/types'
import MainLayout from '@/components/MainLayout.vue'

interface DepartmentListItem extends Department {
  level: number
  hasChildren: boolean
}

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const departmentList = ref<DepartmentListItem[]>([])
const departmentTree = ref<DepartmentTree[]>([])
const employeeOptions = ref<User[]>([])
const formRef = ref<FormInstance>()

const formData = reactive({
  parent_id: 0,
  name: '',
  code: '',
  description: '',
  sort: 0,
  status: 1,
  leader_id: undefined as number | undefined,
})

const rules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
}

const columns = [
  { title: '部门名称', dataIndex: 'name', key: 'name', width: 280 },
  { title: '部门编码', dataIndex: 'code', key: 'code', width: 150 },
  { title: '排序', dataIndex: 'sort', key: 'sort', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
]

const parentOptions = computed(() => {
  const options = [...departmentTree.value]
  if (isEdit.value && editId.value) {
    const filterTree = (items: DepartmentTree[]): DepartmentTree[] => {
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

const flattenTree = (items: DepartmentTree[], level: number = 0): DepartmentListItem[] => {
  const result: DepartmentListItem[] = []
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

const fetchDepartments = async () => {
  loading.value = true
  try {
    const res = await departmentApi.getTree()
    if (res.code === 200) {
      departmentTree.value = res.data
      departmentList.value = flattenTree(res.data)
    }
  } catch (error) {
    console.error('获取部门列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchEmployees = async () => {
  try {
    const res = await employeeApi.getList({ is_active: true })
    if (res.code === 200) {
      employeeOptions.value = res.data
    }
  } catch (error) {
    console.error('获取员工列表失败:', error)
  }
}

const resetForm = () => {
  formData.parent_id = 0
  formData.name = ''
  formData.code = ''
  formData.description = ''
  formData.sort = 0
  formData.status = 1
  formData.leader_id = undefined
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  fetchEmployees()
  modalVisible.value = true
}

const handleEdit = async (record: Department) => {
  isEdit.value = true
  editId.value = record.id
  loading.value = true
  try {
    const [deptRes, empRes] = await Promise.all([
      departmentApi.getById(record.id),
      employeeApi.getList({ is_active: true }),
    ])
    if (deptRes.code === 200) {
      const data = deptRes.data
      formData.parent_id = data.parent_id
      formData.name = data.name
      formData.code = data.code || ''
      formData.description = data.description || ''
      formData.sort = data.sort
      formData.status = data.status
      formData.leader_id = data.leader_id || undefined
    }
    if (empRes.code === 200) {
      employeeOptions.value = empRes.data
    }
    modalVisible.value = true
  } catch (error) {
    console.error('获取部门详情失败:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (record: Department) => {
  try {
    const res = await departmentApi.delete(record.id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchDepartments()
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
      const res = await departmentApi.update(editId.value, { 
        ...formData,
        parent_id: formData.parent_id,
      })
      if (res.code === 200) {
        message.success('更新成功')
        modalVisible.value = false
        fetchDepartments()
      }
    } else {
      const res = await departmentApi.create({
        ...formData,
        parent_id: formData.parent_id,
      })
      if (res.code === 200) {
        message.success('创建成功')
        modalVisible.value = false
        fetchDepartments()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchDepartments()
})
</script>

<style scoped>
.department-page {
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
