<template>
  <div class="change-password-page">
    <div class="page-background">
      <div class="bg-gradient bg-gradient-1"></div>
      <div class="bg-gradient bg-gradient-2"></div>
    </div>

    <div class="page-content">
      <div class="content-wrapper animate-slide-up">
        <div class="page-header">
          <div class="header-back" @click="handleGoBack">
            <LeftOutlined class="back-icon" />
            <span>返回登录</span>
          </div>
        </div>

        <div class="main-card">
          <div class="card-header">
            <div class="header-icon">
              <WarningOutlined class="icon" />
            </div>
            <div class="header-text">
              <h1 class="header-title">修改密码</h1>
              <p class="header-subtitle">检测到默认密码，请立即修改以确保账户安全</p>
            </div>
          </div>

          <a-form
            ref="formRef"
            :model="formState"
            :rules="rules"
            layout="vertical"
            @finish="handleChangePassword"
            class="password-form"
          >
            <a-form-item class="form-item" name="oldPassword" label="当前默认密码">
              <a-input-password
                v-model:value="formState.oldPassword"
                size="large"
                placeholder="请输入当前默认密码"
                class="custom-input"
              >
                <template #prefix>
                  <LockOutlined class="input-icon" />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item class="form-item" name="newPassword" label="新密码">
              <a-input-password
                v-model:value="formState.newPassword"
                size="large"
                placeholder="请输入新密码（至少6位）"
                class="custom-input"
              >
                <template #prefix>
                  <SafetyCertificateOutlined class="input-icon" />
                </template>
              </a-input-password>
              <div class="password-strength" v-if="formState.newPassword.length > 0">
                <div class="strength-indicator">
                  <div
                    class="strength-bar"
                    :class="getPasswordStrengthClass(1)"
                  ></div>
                  <div
                    class="strength-bar"
                    :class="getPasswordStrengthClass(2)"
                  ></div>
                  <div
                    class="strength-bar"
                    :class="getPasswordStrengthClass(3)"
                  ></div>
                  <div
                    class="strength-bar"
                    :class="getPasswordStrengthClass(4)"
                  ></div>
                </div>
                <span class="strength-text">{{ getPasswordStrengthText() }}</span>
              </div>
              <div class="password-hint" v-else>
                <span>密码长度至少6位，建议包含字母、数字和特殊字符</span>
              </div>
            </a-form-item>

            <a-form-item class="form-item" name="confirmPassword" label="确认新密码">
              <a-input-password
                v-model:value="formState.confirmPassword"
                size="large"
                placeholder="请再次输入新密码"
                class="custom-input"
              >
                <template #prefix>
                  <SafetyCertificateOutlined class="input-icon" />
                </template>
              </a-input-password>
              <div class="password-match-hint" v-if="formState.confirmPassword.length > 0">
                <CheckCircleOutlined
                  v-if="formState.newPassword === formState.confirmPassword"
                  class="match-icon match-success"
                />
                <CloseCircleOutlined
                  v-else
                  class="match-icon match-error"
                />
                <span :class="formState.newPassword === formState.confirmPassword ? 'match-success' : 'match-error'">
                  {{ formState.newPassword === formState.confirmPassword ? '两次密码一致' : '两次密码不一致' }}
                </span>
              </div>
            </a-form-item>

            <div class="form-actions">
              <a-button
                type="primary"
                html-type="submit"
                class="submit-btn"
                :loading="loading"
              >
                确认修改密码
              </a-button>
            </div>
          </a-form>

          <div class="card-footer">
            <SafetyCertificateOutlined class="security-icon" />
            <span>密码将通过加密存储，保护您的账户安全</span>
          </div>
        </div>

        <div class="page-copyright">
          <p>© 2026 智现 AgentNow 企业智能体平台</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Modal } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import {
  WarningOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LeftOutlined,
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
  oldPassword: [{ required: true, message: '请输入当前默认密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const passwordStrength = computed(() => {
  const password = formState.newPassword
  if (!password) return 0
  let score = 0
  if (password.length >= 6) score++
  if (password.length >= 10) score++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++
  return Math.min(4, score)
})

const getPasswordStrengthClass = (level: number) => {
  if (passwordStrength.value >= level) {
    if (passwordStrength.value <= 1) return 'weak'
    if (passwordStrength.value <= 2) return 'medium'
    if (passwordStrength.value <= 3) return 'strong'
    return 'excellent'
  }
  return ''
}

const getPasswordStrengthText = () => {
  const strength = passwordStrength.value
  if (strength <= 1) return '弱'
  if (strength <= 2) return '一般'
  if (strength <= 3) return '强'
  return '非常强'
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
        router.push({ name: 'SuperAssistant' })
      },
    })
  } catch (error) {
    console.error('Change password failed:', error)
  } finally {
    loading.value = false
  }
}

const handleGoBack = () => {
  Modal.confirm({
    title: '确认离开',
    content: '您还未修改密码，离开后需要重新登录。确定要离开吗？',
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: () => {
      userStore.logout()
      router.push({ name: 'Login' })
    },
  })
}
</script>

<style scoped>
.change-password-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.page-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-gradient {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.bg-gradient-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(22, 93, 255, 0.5) 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation: float 12s ease-in-out infinite;
}

.bg-gradient-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(114, 46, 209, 0.3) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.page-content {
  position: relative;
  z-index: 10;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.content-wrapper {
  width: 100%;
  max-width: 480px;
}

.page-header {
  margin-bottom: 16px;
}

.header-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.header-back:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.08);
}

.back-icon {
  font-size: 14px;
}

.main-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 28px;
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f2f3f5;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #FFF7E8 0%, #FFE8C8 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-icon .icon {
  font-size: 20px;
  color: #FF7D00;
}

.header-text {
  flex: 1;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0 0 4px 0;
}

.header-subtitle {
  font-size: 13px;
  color: #86909c;
  margin: 0;
}

.password-form {
  animation: fadeIn 0.5s ease-out;
}

.form-item {
  margin-bottom: 16px;
}

:deep(.form-item .ant-form-item-label > label) {
  font-weight: 500;
  color: #4e5969;
  font-size: 13px;
  height: 22px;
}

.input-icon {
  color: #86909c;
  font-size: 16px;
}

:deep(.custom-input .ant-input-affix-wrapper) {
  border-radius: 10px !important;
  border: 1px solid #e5e6eb;
  background: #ffffff;
  padding: 8px 12px;
  font-size: 14px;
  transition: all 0.2s ease;
}

:deep(.custom-input .ant-input-affix-wrapper:hover) {
  border-color: #c9cdd4;
}

:deep(.custom-input .ant-input-affix-wrapper-focused) {
  border-color: #165DFF !important;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1) !important;
  background: #ffffff;
}

:deep(.custom-input .ant-input-affix-wrapper-status-error) {
  border-color: #F53F3F !important;
}

.password-hint {
  margin-top: 6px;
}

.password-hint span {
  font-size: 11px;
  color: #86909c;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.strength-indicator {
  display: flex;
  gap: 4px;
}

.strength-bar {
  width: 28px;
  height: 5px;
  border-radius: 3px;
  background: #f2f3f5;
  transition: all 0.3s ease;
}

.strength-bar.weak {
  background: linear-gradient(90deg, #F53F3F, #FF6565);
}

.strength-bar.medium {
  background: linear-gradient(90deg, #FF7D00, #FF9A2E);
}

.strength-bar.strong {
  background: linear-gradient(90deg, #165DFF, #4080FF);
}

.strength-bar.excellent {
  background: linear-gradient(90deg, #00B42A, #23C343);
}

.strength-text {
  font-size: 11px;
  font-weight: 500;
}

.password-match-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.match-icon {
  font-size: 14px;
}

.match-success {
  color: #00B42A;
}

.match-error {
  color: #F53F3F;
}

.password-match-hint span {
  font-size: 11px;
  font-weight: 500;
}

.form-actions {
  margin-top: 20px;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 10px;
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
  transition: all 0.25s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(22, 93, 255, 0.4);
  background: linear-gradient(135deg, #4080FF 0%, #165DFF 100%);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 4px 8px rgba(22, 93, 255, 0.25);
}

.card-footer {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px solid #f2f3f5;
}

.security-icon {
  color: #00B42A;
  font-size: 14px;
}

.card-footer span {
  font-size: 11px;
  color: #86909c;
}

.page-copyright {
  margin-top: 16px;
  text-align: center;
}

.page-copyright p {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .page-content {
    padding: 16px;
  }

  .main-card {
    padding: 20px;
    border-radius: 12px;
  }

  .header-title {
    font-size: 16px;
  }

  .submit-btn {
    height: 42px;
    font-size: 14px;
  }

  .strength-bar {
    width: 24px;
  }
}
</style>
