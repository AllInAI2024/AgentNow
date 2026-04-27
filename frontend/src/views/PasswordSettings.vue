<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <div class="layout-logo" @click="handleGoHome" style="cursor: pointer;">
        <RobotOutlined class="layout-logo-icon" />
        <span class="layout-logo-text">智现 AgentNow</span>
      </div>
      <div class="user-info">
        <a-dropdown :trigger="['click']">
          <div class="user-dropdown-trigger">
            <a-avatar class="user-avatar" :size="36">
              {{ userStore.userInfo?.username?.charAt(0) }}
            </a-avatar>
            <span class="user-name">{{ userStore.userInfo?.username }}</span>
            <DownOutlined :style="{ fontSize: '12px', color: '#8c8c8c', marginLeft: '4px' }" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="dashboard" @click="handleGoHome">
                <DashboardOutlined />
                <span>工作台</span>
              </a-menu-item>
              <a-menu-item key="logout" @click="handleLogout">
                <LogoutOutlined />
                <span>退出登录</span>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </a-layout-header>

    <a-layout-content class="layout-content">
      <div class="settings-container">
        <a-card class="settings-card" :bordered="false">
          <div class="settings-header">
            <h2 class="settings-title">修改密码</h2>
            <p class="settings-subtitle">修改您的登录密码以保障账户安全</p>
          </div>

          <a-form
            ref="formRef"
            :model="formState"
            :rules="rules"
            layout="vertical"
            @finish="handleChangePassword"
            class="settings-form"
          >
            <a-form-item class="form-item" name="oldPassword" label="当前密码">
              <a-input-password
                v-model:value="formState.oldPassword"
                size="large"
                placeholder="请输入当前密码"
              >
                <template #prefix>
                  <LockOutlined style="color: rgba(0, 0, 0, 0.45)" />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item class="form-item" name="newPassword" label="新密码">
              <a-input-password
                v-model:value="formState.newPassword"
                size="large"
                placeholder="请输入新密码（至少6位）"
              >
                <template #prefix>
                  <SafetyCertificateOutlined style="color: rgba(0, 0, 0, 0.45)" />
                </template>
              </a-input-password>
              <div class="password-hint">
                密码长度至少6位，建议包含字母、数字和特殊字符
              </div>
            </a-form-item>

            <a-form-item class="form-item" name="confirmPassword" label="确认新密码">
              <a-input-password
                v-model:value="formState.confirmPassword"
                size="large"
                placeholder="请再次输入新密码"
              >
                <template #prefix>
                  <SafetyCertificateOutlined style="color: rgba(0, 0, 0, 0.45)" />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item class="form-actions">
              <a-button
                type="primary"
                html-type="submit"
                class="submit-btn"
                :loading="loading"
              >
                {{ loading ? '提交中...' : '确认修改' }}
              </a-button>
              <a-button class="cancel-btn" @click="handleGoHome">
                取消
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </div>
    </a-layout-content>

    <a-layout-footer class="layout-footer">
      <span>© 2026 智现 AgentNow 企业智能体平台</span>
    </a-layout-footer>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import {
  RobotOutlined,
  DownOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  LogoutOutlined,
  DashboardOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formState = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: Rule, value: string) => {
  if (!value) {
    return Promise.reject('请再次输入新密码')
  }
  if (value !== formState.newPassword) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const rules: Record<string, Rule[]> = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleChangePassword = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await userStore.changePassword(formState.oldPassword, formState.newPassword)
    
    Modal.success({
      title: '密码修改成功',
      content: '您的密码已成功修改。',
      okText: '确定',
      onOk: () => {
        formState.oldPassword = ''
        formState.newPassword = ''
        formState.confirmPassword = ''
        formRef.value?.resetFields()
      },
    })
  } catch (error) {
    console.error('Change password failed:', error)
  } finally {
    loading.value = false
  }
}

const handleGoHome = () => {
  router.push({ name: 'Dashboard' })
}

const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '确定要退出登录吗？',
    okText: '确定',
    cancelText: '取消',
    onOk: () => {
      userStore.logout()
      router.push({ name: 'Login' })
      message.success('已退出登录')
    },
  })
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  height: 64px;
  line-height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.layout-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.layout-logo-icon {
  font-size: 28px;
  color: var(--primary-color, #1890ff);
}

.layout-logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 8px;
  border-radius: 6px;
  transition: background 0.3s;
}

.user-dropdown-trigger:hover {
  background: #f5f5f5;
}

.user-avatar {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: #262626;
  margin-left: 8px;
  font-weight: 500;
}

.layout-content {
  margin: 24px 32px;
  padding: 0;
  background: transparent;
}

.settings-container {
  max-width: 600px;
  margin: 0 auto;
}

.settings-card {
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.settings-header {
  text-align: center;
  margin-bottom: 32px;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.settings-subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.settings-form {
  max-width: 400px;
  margin: 0 auto;
}

.form-item {
  margin-bottom: 24px;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  color: #262626;
}

:deep(.ant-input-affix-wrapper) {
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 15px;
}

:deep(.ant-input-affix-wrapper-focused) {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.15);
}

.password-hint {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.form-actions {
  margin-top: 32px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.submit-btn {
  width: 140px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.35);
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.45);
}

.cancel-btn {
  width: 140px;
  height: 48px;
  font-size: 16px;
  border-radius: 10px;
}

.layout-footer {
  text-align: center;
  color: #8c8c8c;
  font-size: 12px;
  padding: 24px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}
</style>
