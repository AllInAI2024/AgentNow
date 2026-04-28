<template>
  <div class="change-password-container">
    <a-card class="change-password-card" :bordered="false">
      <div class="header">
        <div class="warning-icon">
          <WarningOutlined :style="{ fontSize: '36px', color: '#faad14' }" />
        </div>
        <h1 class="title">修改密码</h1>
        <p class="subtitle">您正在使用默认密码，请立即修改以确保账户安全</p>
      </div>

      <a-alert
        message="安全提醒"
        description="检测到您正在使用系统默认密码，为了账户安全，请修改为新密码后再继续使用。"
        type="warning"
        show-icon
        class="warning-alert"
      />

      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
        @finish="handleChangePassword"
      >
        <a-form-item class="form-item" name="oldPassword" label="原密码">
          <a-input-password
            v-model:value="formState.oldPassword"
            size="large"
            placeholder="请输入原密码"
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

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            class="submit-btn"
            :loading="loading"
          >
            {{ loading ? '提交中...' : '确认修改' }}
          </a-button>
        </a-form-item>
      </a-form>

      <div class="footer">
        <a-button type="link" @click="handleLogout">
          <LogoutOutlined /> 退出登录
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import {
  WarningOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  LogoutOutlined,
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
  if (value && value !== formState.newPassword) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const rules: Record<string, Rule[]> = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
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
      content: '您的密码已成功修改，即将跳转到工作台...',
      okText: '确定',
      onOk: () => {
        router.push({ name: 'Dashboard' })
      },
    })
  } catch (error) {
    console.error('Change password failed:', error)
  } finally {
    loading.value = false
  }
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
    },
  })
}
</script>

<style scoped>
.change-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.change-password-container::before {
  content: '';
  position: absolute;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  animation: float 25s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-5%, -5%) rotate(5deg); }
}

.change-password-card {
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
}

.header {
  text-align: center;
  margin-bottom: 24px;
}

.warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #fffbe6 0%, #ffe58f 100%);
  border-radius: 50%;
  margin-bottom: 16px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.warning-alert {
  margin-bottom: 32px;
  border-radius: 10px;
}

:deep(.ant-alert-message) {
  font-weight: 600;
  color: #d48806;
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

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  letter-spacing: 2px;
  margin-top: 8px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.35);
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.45);
}

.footer {
  margin-top: 24px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.footer :deep(.ant-btn-link) {
  color: #999;
  font-size: 14px;
}

.footer :deep(.ant-btn-link:hover) {
  color: #1890ff;
}
</style>
