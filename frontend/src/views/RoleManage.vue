<template>
  <MainLayout>
    <div class="role-page">
      <a-card class="page-card">
        <template #title>
          <div class="page-header">
            <span class="page-title">角色管理</span>
            <a-button type="primary" @click="handleAdd">
              <PlusOutlined /> 新增角色
            </a-button>
          </div>
        </template>

        <a-table
          :columns="columns"
          :data-source="roleList"
          :loading="loading"
          row-key="id"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="handleEdit(record)">
                  编辑
                </a-button>
                <a-button type="link" size="small" @click="handleAssignPermission(record)">
                  权限配置
                </a-button>
                <a-popconfirm
                  title="确定要删除该角色吗？"
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
        :title="isEdit ? '编辑角色' : '新增角色'"
        :width="640"
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
          <a-form-item label="角色名称" name="name">
            <a-input
              v-model:value="formData.name"
              placeholder="请输入角色名称"
            />
          </a-form-item>
          <a-form-item label="角色编码" name="code">
            <a-input
              v-model:value="formData.code"
              placeholder="请输入角色编码（英文标识，如：manager）"
              :disabled="isEdit"
            />
          </a-form-item>
          <a-form-item label="角色描述" name="description">
            <a-textarea
              v-model:value="formData.description"
              placeholder="请输入角色描述"
              :rows="3"
            />
          </a-form-item>
        </a-form>
      </a-modal>

      <a-modal
        v-model:open="permissionModalVisible"
        title="权限配置"
        :width="720"
        @ok="handleSubmitPermission"
        @cancel="handleCancelPermission"
        :confirmLoading="submittingPermission"
      >
        <div class="permission-config">
          <a-tree
            v-model:checkedKeys="checkedPermissionKeys"
            :tree-data="permissionTreeData"
            :replace-fields="{ children: 'children', title: 'name', key: 'id', value: 'id' }"
            checkable
            :default-expand-all="true"
            :check-strictly="false"
          />
        </div>
      </a-modal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { roleApi, type Role } from '@/api/role'
import { permissionApi, type PermissionTree } from '@/api/permission'
import MainLayout from '@/components/MainLayout.vue'

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const roleList = ref<Role[]>([])
const formRef = ref<FormInstance>()

const permissionModalVisible = ref(false)
const submittingPermission = ref(false)
const currentRoleId = ref<number | null>(null)
const permissionTree = ref<PermissionTree[]>([])
const checkedPermissionKeys = ref<number[]>([])

const formData = reactive({
  name: '',
  code: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
}

const columns = [
  { title: '角色名称', dataIndex: 'name', key: 'name', width: 150 },
  { title: '角色编码', dataIndex: 'code', key: 'code', width: 180 },
  { title: '角色描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' as const },
]

const permissionTreeData = computed(() => {
  return permissionTree.value
})

const fetchRoles = async () => {
  loading.value = true
  try {
    const res = await roleApi.getList()
    if (res.code === 200) {
      roleList.value = res.data
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchPermissions = async () => {
  try {
    const res = await permissionApi.getTree()
    if (res.code === 200) {
      permissionTree.value = res.data
    }
  } catch (error) {
    console.error('获取权限列表失败:', error)
  }
}

const resetForm = () => {
  formData.name = ''
  formData.code = ''
  formData.description = ''
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  modalVisible.value = true
}

const handleEdit = async (record: Role) => {
  isEdit.value = true
  editId.value = record.id
  loading.value = true
  try {
    const res = await roleApi.getById(record.id)
    if (res.code === 200) {
      const data = res.data
      formData.name = data.name
      formData.code = data.code
      formData.description = data.description || ''
      modalVisible.value = true
    }
  } catch (error) {
    console.error('获取角色详情失败:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (record: Role) => {
  try {
    const res = await roleApi.delete(record.id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchRoles()
    }
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleAssignPermission = async (record: Role) => {
  currentRoleId.value = record.id
  checkedPermissionKeys.value = []
  
  try {
    const res = await roleApi.getPermissions(record.id)
    if (res.code === 200) {
      checkedPermissionKeys.value = res.data
    }
    permissionModalVisible.value = true
  } catch (error) {
    console.error('获取角色权限失败:', error)
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
  resetForm()
}

const handleCancelPermission = () => {
  permissionModalVisible.value = false
  currentRoleId.value = null
  checkedPermissionKeys.value = []
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
        name: formData.name,
        description: formData.description || undefined,
      }
      const res = await roleApi.update(editId.value, updateData)
      if (res.code === 200) {
        message.success('更新成功')
        modalVisible.value = false
        fetchRoles()
      }
    } else {
      const createData = {
        name: formData.name,
        code: formData.code,
        description: formData.description || undefined,
      }
      const res = await roleApi.create(createData)
      if (res.code === 200) {
        message.success('创建成功')
        modalVisible.value = false
        fetchRoles()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleSubmitPermission = async () => {
  if (!currentRoleId.value) return

  submittingPermission.value = true
  try {
    const res = await roleApi.assignPermissions(currentRoleId.value, checkedPermissionKeys.value)
    if (res.code === 200) {
      message.success('权限配置成功')
      permissionModalVisible.value = false
    }
  } catch (error) {
    console.error('权限配置失败:', error)
  } finally {
    submittingPermission.value = false
  }
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<style scoped>
.role-page {
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

.permission-config {
  max-height: 500px;
  overflow-y: auto;
}
</style>
