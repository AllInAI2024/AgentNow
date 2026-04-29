<template>
  <MainLayout>
    <div class="employee-page">
      <a-card class="page-card">
        <template #title>
          <div class="page-header">
            <span class="page-title">员工管理</span>
            <a-button type="primary" @click="handleAdd">
              <PlusOutlined /> 新增员工
            </a-button>
          </div>
        </template>

        <div class="search-bar">
          <a-form layout="inline" :model="searchForm">
            <a-form-item label="部门">
              <a-select
                v-model:value="searchForm.department_id"
                :options="departmentOptions"
                placeholder="全部部门"
                allow-clear
                :field-names="{ label: 'name', value: 'id' }"
                style="width: 200px"
                @change="handleSearch"
              />
            </a-form-item>
            <a-form-item label="状态">
              <a-select
                v-model:value="searchForm.is_active"
                placeholder="全部状态"
                allow-clear
                style="width: 120px"
                @change="handleSearch"
              >
                <a-select-option :value="true">启用</a-select-option>
                <a-select-option :value="false">禁用</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>

        <a-table
          :columns="columns"
          :data-source="employeeList"
          :loading="loading"
          row-key="id"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'department'">
              {{ getDepartmentName(record.department_id) }}
            </template>
            <template v-else-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'red'">
                {{ record.is_active ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'is_default_password'">
              <a-tag v-if="record.is_default_password" color="orange">
                需改密码
              </a-tag>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space size="small">
                <a-tooltip title="编辑">
                  <a-button type="text" size="small" @click="handleEdit(record)">
                    <EditOutlined />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="分配角色">
                  <a-button type="text" size="small" @click="handleAssignRole(record)">
                    <SafetyCertificateOutlined />
                  </a-button>
                </a-tooltip>
                <a-popconfirm
                  title="确定要重置密码吗？重置后密码为123456。"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleResetPassword(record)"
                >
                  <a-tooltip title="重置密码">
                    <a-button type="text" size="small">
                      <KeyOutlined />
                    </a-button>
                  </a-tooltip>
                </a-popconfirm>
                <a-popconfirm
                  :title="record.is_active ? '确定要禁用该员工吗？' : '确定要启用该员工吗？'"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleToggleStatus(record)"
                >
                  <a-tooltip :title="record.is_active ? '禁用' : '启用'">
                    <a-button type="text" size="small" :danger="record.is_active">
                      <component :is="record.is_active ? StopOutlined : PlayCircleOutlined" />
                    </a-button>
                  </a-tooltip>
                </a-popconfirm>
                <a-popconfirm
                  title="确定要删除该员工吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a-tooltip title="删除">
                    <a-button type="text" size="small" danger>
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
        :title="isEdit ? '编辑员工' : '新增员工'"
        :width="720"
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
              <a-form-item label="所属部门" name="department_id">
                <a-select
                  v-model:value="formData.department_id"
                  :options="departmentOptions"
                  placeholder="请选择所属部门"
                  :field-names="{ label: 'name', value: 'id' }"
                  style="width: 100%"
                >
                  <template #notFoundContent>
                    <div class="empty-tip">
                      暂无部门数据，请先添加部门
                    </div>
                  </template>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="登录账号" name="login_name">
                <a-input
                  v-model:value="formData.login_name"
                  placeholder="请输入登录账号"
                  :disabled="isEdit"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="员工姓名" name="username">
                <a-input
                  v-model:value="formData.username"
                  placeholder="请输入员工姓名"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="手机号" name="phone">
                <a-input
                  v-model:value="formData.phone"
                  placeholder="请输入手机号（可用于登录）"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24">
            <a-col :span="12">
              <a-form-item label="邮箱" name="email">
                <a-input
                  v-model:value="formData.email"
                  placeholder="请输入邮箱"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12" v-if="!isEdit">
              <a-form-item label="初始密码" name="password">
                <a-input-password
                  v-model:value="formData.password"
                  placeholder="不填则默认为123456"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="24" v-if="isEdit">
            <a-col :span="12">
              <a-form-item label="状态" name="is_active">
                <a-select v-model:value="formData.is_active" placeholder="请选择状态">
                  <a-select-option :value="true">启用</a-select-option>
                  <a-select-option :value="false">禁用</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </a-modal>

      <a-modal
        v-model:open="roleModalVisible"
        title="分配角色"
        :width="640"
        @ok="handleSubmitRole"
        @cancel="handleCancelRole"
        :confirmLoading="submittingRole"
      >
        <div class="role-select-container">
          <a-checkbox-group v-model:value="selectedRoleIds">
            <a-space direction="vertical" size="middle" style="width: 100%">
              <a-checkbox v-for="role in roleList" :key="role.id" :value="role.id">
                <span class="role-name">{{ role.name }}</span>
                <span class="role-code">({{ role.code }})</span>
                <span v-if="role.description" class="role-desc">- {{ role.description }}</span>
              </a-checkbox>
            </a-space>
          </a-checkbox-group>
        </div>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SafetyCertificateOutlined,
  KeyOutlined,
  StopOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons-vue'
import { employeeApi } from '@/api/employee'
import { departmentApi } from '@/api/department'
import { roleApi, type Role } from '@/api/role'
import type { User, DepartmentTree } from '@/types'
import MainLayout from '@/components/MainLayout.vue'

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const employeeList = ref<User[]>([])
const departmentTree = ref<DepartmentTree[]>([])
const formRef = ref<FormInstance>()

const roleModalVisible = ref(false)
const submittingRole = ref(false)
const currentEmployeeId = ref<number | null>(null)
const roleList = ref<Role[]>([])
const selectedRoleIds = ref<number[]>([])

const searchForm = reactive({
  department_id: undefined as number | undefined,
  is_active: undefined as boolean | undefined,
})

const formData = reactive({
  department_id: undefined as number | undefined,
  login_name: '',
  username: '',
  phone: '',
  email: '',
  password: '',
  is_active: true,
})

const rules = {
  department_id: [{ required: true, message: '请选择所属部门', trigger: 'change' }],
  login_name: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入员工姓名', trigger: 'blur' }],
}

const columns = [
  { title: '登录账号', dataIndex: 'login_name', key: 'login_name', width: 150 },
  { title: '员工姓名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '部门', key: 'department', width: 150 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 140 },
  { title: '邮箱', dataIndex: 'email', key: 'email', ellipsis: true },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '密码状态', dataIndex: 'is_default_password', key: 'is_default_password', width: 100 },
  { title: '操作', key: 'action', width: 420, fixed: 'right' as const },
]

const getAllDepartments = (items: DepartmentTree[]): DepartmentTree[] => {
  const result: DepartmentTree[] = []
  items.forEach(item => {
    result.push(item)
    if (item.children && item.children.length > 0) {
      result.push(...getAllDepartments(item.children))
    }
  })
  return result
}

const getDepartmentName = (deptId: number | null): string => {
  if (!deptId) return '-'
  const allDepts = getAllDepartments(departmentTree.value)
  const dept = allDepts.find(d => d.id === deptId)
  return dept ? dept.name : '-'
}

const departmentOptions = computed(() => {
  const flattenWithIndent = (items: DepartmentTree[], level: number = 0): Array<{ id: number; name: string }> => {
    const result: Array<{ id: number; name: string }> = []
    items.forEach(item => {
      const indent = '　'.repeat(level * 2)
      result.push({
        id: item.id,
        name: level > 0 ? `${indent}└ ${item.name}` : item.name,
      })
      if (item.children && item.children.length > 0) {
        result.push(...flattenWithIndent(item.children, level + 1))
      }
    })
    return result
  }
  
  return flattenWithIndent(departmentTree.value)
})

const fetchEmployees = async () => {
  loading.value = true
  try {
    const params: { department_id?: number; is_active?: boolean } = {}
    if (searchForm.department_id !== undefined) {
      params.department_id = searchForm.department_id
    }
    if (searchForm.is_active !== undefined) {
      params.is_active = searchForm.is_active
    }
    const res = await employeeApi.getList(params)
    if (res.code === 200) {
      employeeList.value = res.data
    }
  } catch (error) {
    console.error('获取员工列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchDepartments = async () => {
  try {
    const res = await departmentApi.getTree()
    if (res.code === 200) {
      departmentTree.value = res.data
    }
  } catch (error) {
    console.error('获取部门列表失败:', error)
  }
}

const resetForm = () => {
  formData.department_id = undefined
  formData.login_name = ''
  formData.username = ''
  formData.phone = ''
  formData.email = ''
  formData.password = ''
  formData.is_active = true
}

const handleSearch = () => {
  fetchEmployees()
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  modalVisible.value = true
}

const handleEdit = async (record: User) => {
  isEdit.value = true
  editId.value = record.id
  loading.value = true
  try {
    const res = await employeeApi.getById(record.id)
    if (res.code === 200) {
      const data = res.data
      formData.department_id = data.department_id || undefined
      formData.login_name = data.login_name
      formData.username = data.username
      formData.phone = data.phone || ''
      formData.email = data.email || ''
      formData.is_active = data.is_active
      modalVisible.value = true
    }
  } catch (error) {
    console.error('获取员工详情失败:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (record: User) => {
  try {
    const res = await employeeApi.delete(record.id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchEmployees()
    }
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleResetPassword = async (record: User) => {
  try {
    const res = await employeeApi.resetPassword(record.id)
    if (res.code === 200) {
      message.success('密码已重置为123456')
      fetchEmployees()
    }
  } catch (error) {
    console.error('重置密码失败:', error)
  }
}

const handleToggleStatus = async (record: User) => {
  try {
    const res = await employeeApi.toggleStatus(record.id)
    if (res.code === 200) {
      message.success(`已${record.is_active ? '禁用' : '启用'}`)
      fetchEmployees()
    }
  } catch (error) {
    console.error('状态切换失败:', error)
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
      const updateData = {
        department_id: formData.department_id,
        username: formData.username,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        is_active: formData.is_active,
      }
      const res = await employeeApi.update(editId.value, updateData)
      if (res.code === 200) {
        message.success('更新成功')
        modalVisible.value = false
        fetchEmployees()
      }
    } else {
      const createData = {
        department_id: formData.department_id!,
        login_name: formData.login_name,
        username: formData.username,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        password: formData.password || undefined,
      }
      const res = await employeeApi.create(createData)
      if (res.code === 200) {
        message.success('创建成功，默认密码为123456')
        modalVisible.value = false
        fetchEmployees()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const fetchRoles = async () => {
  try {
    const res = await roleApi.getList()
    if (res.code === 200) {
      roleList.value = res.data
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

const handleAssignRole = async (record: User) => {
  currentEmployeeId.value = record.id
  selectedRoleIds.value = []
  
  try {
    const res = await roleApi.getUserRoles(record.id)
    if (res.code === 200) {
      selectedRoleIds.value = res.data
    }
    roleModalVisible.value = true
  } catch (error) {
    console.error('获取用户角色失败:', error)
  }
}

const handleCancelRole = () => {
  roleModalVisible.value = false
  currentEmployeeId.value = null
  selectedRoleIds.value = []
}

const handleSubmitRole = async () => {
  if (!currentEmployeeId.value) return

  submittingRole.value = true
  try {
    const res = await roleApi.assignUserRoles(currentEmployeeId.value, selectedRoleIds.value)
    if (res.code === 200) {
      message.success('角色分配成功')
      roleModalVisible.value = false
    }
  } catch (error) {
    console.error('角色分配失败:', error)
  } finally {
    submittingRole.value = false
  }
}

onMounted(() => {
  fetchDepartments()
  fetchEmployees()
  fetchRoles()
})
</script>

<style scoped>
.employee-page {
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

.search-bar {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}

.action-buttons .ant-btn-link {
  white-space: nowrap;
  padding: 4px 8px;
}

.role-select-container {
  max-height: 400px;
  overflow-y: auto;
}

.role-name {
  font-weight: 500;
  color: #1d2129;
}

.role-code {
  color: #86909c;
  font-size: 12px;
  margin-left: 4px;
}

.role-desc {
  color: #86909c;
  font-size: 12px;
  margin-left: 8px;
}
</style>
