<template>
  <div class="settings-page">
    <a-layout class="layout-container">
      <a-layout-header class="layout-header">
        <div class="header-left">
          <div class="logo-wrapper" @click="handleGoHome" style="cursor: pointer;">
            <div class="logo-icon">
              <RobotOutlined class="logo-robot" />
            </div>
            <div class="logo-text">
              <span class="logo-brand">智现</span>
              <span class="logo-name">AgentNow</span>
            </div>
          </div>
        </div>

        <div class="header-center">
          <div class="search-bar">
            <SearchOutlined class="search-icon" />
            <input
              type="text"
              class="search-input"
              placeholder="搜索智能体、文档或功能..."
            />
            <span class="search-hint">⌘K</span>
          </div>
        </div>

        <div class="header-right">
          <div class="header-actions">
            <a-tooltip title="消息通知">
              <div class="action-btn notification-btn">
                <BellOutlined class="action-icon" />
                <span class="notification-badge"></span>
              </div>
            </a-tooltip>

            <a-tooltip title="帮助中心">
              <div class="action-btn">
                <QuestionCircleOutlined class="action-icon" />
              </div>
            </a-tooltip>

            <a-divider type="vertical" class="header-divider" />

            <a-dropdown :trigger="['click']" placement="bottomRight">
              <div class="user-dropdown-trigger">
                <a-avatar class="user-avatar" :size="36">
                  {{ userStore.userInfo?.username?.charAt(0) }}
                </a-avatar>
                <div class="user-info-text">
                  <span class="user-name">{{ userStore.userInfo?.username }}</span>
                  <span class="user-role">员工</span>
                </div>
                <DownOutlined class="dropdown-arrow" />
              </div>
              <template #overlay>
                <a-menu class="user-dropdown-menu">
                  <div class="dropdown-user-info">
                    <a-avatar class="dropdown-avatar" :size="48">
                      {{ userStore.userInfo?.username?.charAt(0) }}
                    </a-avatar>
                    <div class="dropdown-user-detail">
                      <span class="dropdown-username">{{ userStore.userInfo?.username }}</span>
                      <span class="dropdown-email">{{ userStore.userInfo?.phone }}</span>
                    </div>
                  </div>
                  <a-menu-divider />
                  <a-menu-item key="dashboard" @click="handleGoHome">
                    <DashboardOutlined class="menu-icon" />
                    <span>工作台</span>
                  </a-menu-item>
                  <a-menu-item key="profile" @click="handleProfile">
                    <UserOutlined class="menu-icon" />
                    <span>个人中心</span>
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="logout" @click="handleLogout" class="menu-item-danger">
                    <LogoutOutlined class="menu-icon" />
                    <span>退出登录</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
      </a-layout-header>

      <a-layout-content class="layout-content">
        <div class="page-nav animate-slide-up">
          <a-breadcrumb class="breadcrumb">
            <a-breadcrumb-item @click="handleGoHome" style="cursor: pointer;">
              <HomeOutlined class="breadcrumb-icon" />
              <span>工作台</span>
            </a-breadcrumb-item>
            <a-breadcrumb-item>账户设置</a-breadcrumb-item>
            <a-breadcrumb-item>修改密码</a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <div class="settings-container animate-slide-up" style="animation-delay: 0.05s;">
          <div class="settings-card">
            <div class="settings-header">
              <div class="header-icon-wrapper">
                <SafetyCertificateOutlined class="header-icon" />
              </div>
              <div class="header-text">
                <h2 class="settings-title">修改密码</h2>
                <p class="settings-subtitle">修改您的登录密码以保障账户安全</p>
              </div>
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
                <div class="input-field-wrapper">
                  <a-input-password
                    v-model:value="formState.oldPassword"
                    size="large"
                    placeholder="请输入当前密码"
                    class="custom-input"
                  >
                    <template #prefix>
                      <LockOutlined class="input-prefix-icon" />
                    </template>
                  </a-input-password>
                </div>
              </a-form-item>

              <div class="form-divider">
                <div class="divider-line"></div>
                <span class="divider-text">设置新密码</span>
                <div class="divider-line"></div>
              </div>

              <a-form-item class="form-item" name="newPassword" label="新密码">
                <div class="input-field-wrapper">
                  <a-input-password
                    v-model:value="formState.newPassword"
                    size="large"
                    placeholder="请输入新密码（至少6位）"
                    class="custom-input"
                  >
                    <template #prefix>
                      <SafetyCertificateOutlined class="input-prefix-icon" />
                    </template>
                  </a-input-password>
                </div>
                <div class="password-hint">
                  <div class="hint-icon">
                    <InfoCircleOutlined />
                  </div>
                  <span>密码长度至少6位，建议包含字母、数字和特殊字符</span>
                </div>
                <div class="password-strength" v-if="formState.newPassword.length > 0">
                  <span class="strength-label">密码强度：</span>
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
              </a-form-item>

              <a-form-item class="form-item" name="confirmPassword" label="确认新密码">
                <div class="input-field-wrapper">
                  <a-input-password
                    v-model:value="formState.confirmPassword"
                    size="large"
                    placeholder="请再次输入新密码"
                    class="custom-input"
                  >
                    <template #prefix>
                      <SafetyCertificateOutlined class="input-prefix-icon" />
                    </template>
                  </a-input-password>
                </div>
                <div class="password-match-hint" v-if="formState.confirmPassword.length > 0">
                  <CheckCircleOutlined
                    v-if="formState.newPassword === formState.confirmPassword && formState.newPassword.length > 0"
                    class="match-icon match-success"
                  />
                  <CloseCircleOutlined
                    v-else-if="formState.confirmPassword.length > 0"
                    class="match-icon match-error"
                  />
                  <span :class="formState.newPassword === formState.confirmPassword && formState.newPassword.length > 0 ? 'match-success' : 'match-error'">
                    {{ formState.newPassword === formState.confirmPassword && formState.newPassword.length > 0 ? '两次密码一致' : '两次密码不一致' }}
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
                  <template #icon v-if="!loading">
                    <SafetyCertificateOutlined />
                  </template>
                  {{ loading ? '提交中...' : '确认修改' }}
                </a-button>
                <a-button class="cancel-btn" @click="handleGoHome">
                  <template #icon>
                    <CloseOutlined />
                  </template>
                  取消
                </a-button>
              </div>
            </a-form>

            <div class="settings-footer">
              <div class="security-tips">
                <div class="tip-item">
                  <div class="tip-icon tip-success">
                    <SafetyCertificateOutlined />
                  </div>
                  <div class="tip-text">
                    <span class="tip-title">安全存储</span>
                    <span class="tip-desc">密码经过加密存储，无法直接读取</span>
                  </div>
                </div>
                <div class="tip-item">
                  <div class="tip-icon tip-warning">
                    <InfoCircleOutlined />
                  </div>
                  <div class="tip-text">
                    <span class="tip-title">密码建议</span>
                    <span class="tip-desc">定期更换密码，避免使用相同密码</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-layout-content>

      <a-layout-footer class="layout-footer">
        <div class="footer-content">
          <div class="footer-left">
            <span class="footer-copyright">© 2026 智现 AgentNow 企业智能体平台</span>
          </div>
          <div class="footer-right">
            <a href="#" class="footer-link">隐私政策</a>
            <a href="#" class="footer-link">服务条款</a>
            <a href="#" class="footer-link">帮助中心</a>
            <span class="footer-version">版本 v1.0.0</span>
          </div>
        </div>
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
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
  SearchOutlined,
  BellOutlined,
  QuestionCircleOutlined,
  UserOutlined,
  HomeOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloseOutlined,
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

const handleProfile = () => {
  message.info('个人中心功能开发中...')
}

const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '确定要退出登录吗？',
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: () => {
      userStore.logout()
      router.push({ name: 'Login' })
      message.success('已退出登录')
    },
  })
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f8fa 0%, #f2f3f5 100%);
}

.layout-container {
  min-height: 100vh;
  background: transparent;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.25);
}

.logo-robot {
  font-size: 20px;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-brand {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.logo-name {
  font-size: 12px;
  font-weight: 500;
  color: #86909c;
}

.header-center {
  flex: 1;
  max-width: 480px;
  padding: 0 32px;
}

.search-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #f7f8fa;
  border-radius: 12px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.search-bar:focus-within {
  background: #ffffff;
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.08);
}

.search-icon {
  color: #86909c;
  font-size: 16px;
  margin-right: 8px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #1d2129;
  outline: none;
}

.search-input::placeholder {
  color: #c9cdd4;
}

.search-hint {
  font-size: 11px;
  color: #86909c;
  background: rgba(0, 0, 0, 0.04);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.action-btn:hover {
  background: #f2f3f5;
}

.action-icon {
  font-size: 18px;
  color: #4e5969;
  transition: color 0.2s ease;
}

.action-btn:hover .action-icon {
  color: #165DFF;
}

.notification-btn .notification-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  background: #F53F3F;
  border-radius: 50%;
  border: 2px solid white;
}

.header-divider {
  height: 24px;
  margin: 0 8px;
  background: #e5e6eb;
}

.user-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.user-dropdown-trigger:hover {
  background: #f2f3f5;
}

.user-avatar {
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(22, 93, 255, 0.25);
}

.user-info-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  line-height: 1.2;
}

.user-role {
  font-size: 12px;
  color: #86909c;
  line-height: 1.2;
}

.dropdown-arrow {
  font-size: 12px;
  color: #86909c;
  transition: transform 0.2s ease;
}

.user-dropdown-trigger:hover .dropdown-arrow {
  color: #4e5969;
}

:deep(.user-dropdown-menu) {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e6eb;
  padding: 8px;
  min-width: 240px;
}

.dropdown-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.dropdown-avatar {
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  font-weight: 600;
}

.dropdown-user-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dropdown-username {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.dropdown-email {
  font-size: 13px;
  color: #86909c;
}

:deep(.user-dropdown-menu .ant-menu-item) {
  border-radius: 8px;
  margin: 4px 0;
  padding: 8px 12px;
}

.menu-icon {
  margin-right: 10px;
  font-size: 16px;
  color: #4e5969;
}

.menu-item-danger {
  color: #F53F3F !important;
}

.menu-item-danger .menu-icon {
  color: #F53F3F !important;
}

.layout-content {
  margin: 0;
  padding: 24px 32px;
  background: transparent;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

.page-nav {
  margin-bottom: 24px;
}

.breadcrumb {
  font-size: 14px;
}

.breadcrumb-icon {
  margin-right: 4px;
  color: #86909c;
}

.settings-container {
  width: 100%;
}

.settings-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e6eb;
}

.settings-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 36px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f2f3f5;
}

.header-icon-wrapper {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #E8F3FF 0%, #D0E8FF 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-icon {
  font-size: 32px;
  color: #165DFF;
}

.header-text {
  flex: 1;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 8px 0;
}

.settings-subtitle {
  font-size: 14px;
  color: #86909c;
  margin: 0;
}

.settings-form {
  max-width: 440px;
  margin: 0 auto;
}

.form-item {
  margin-bottom: 24px;
}

:deep(.form-item .ant-form-item-label > label) {
  font-weight: 500;
  color: #4e5969;
  font-size: 14px;
}

.input-field-wrapper {
  position: relative;
}

.input-prefix-icon {
  color: #86909c;
  font-size: 16px;
}

:deep(.custom-input .ant-input-affix-wrapper) {
  border-radius: 12px !important;
  border: 1px solid #e5e6eb;
  background: #ffffff;
  padding: 10px 14px;
  font-size: 15px;
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
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
}

.hint-icon {
  color: #86909c;
  font-size: 14px;
  margin-top: 1px;
}

.password-hint span {
  font-size: 12px;
  color: #86909c;
  line-height: 1.5;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.strength-label {
  font-size: 12px;
  color: #86909c;
  font-weight: 500;
}

.strength-indicator {
  display: flex;
  gap: 4px;
}

.strength-bar {
  width: 32px;
  height: 6px;
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
  font-size: 12px;
  font-weight: 600;
}

.password-match-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.match-icon {
  font-size: 16px;
}

.match-success {
  color: #00B42A;
}

.match-error {
  color: #F53F3F;
}

.password-match-hint span {
  font-size: 12px;
  font-weight: 500;
}

.form-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 28px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e5e6eb, transparent);
}

.divider-text {
  font-size: 12px;
  font-weight: 600;
  color: #86909c;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-actions {
  margin-top: 36px;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.submit-btn {
  width: 160px;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 12px;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.35);
  transition: all 0.25s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(22, 93, 255, 0.45);
  background: linear-gradient(135deg, #4080FF 0%, #165DFF 100%);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
}

.cancel-btn {
  width: 140px;
  height: 48px;
  font-size: 15px;
  border-radius: 12px;
  border-color: #e5e6eb;
  transition: all 0.2s ease;
}

.cancel-btn:hover:not(:disabled) {
  color: #165DFF;
  border-color: #165DFF;
  background: #E8F3FF;
}

.settings-footer {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #f2f3f5;
}

.security-tips {
  display: flex;
  gap: 32px;
  justify-content: center;
  flex-wrap: wrap;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tip-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tip-icon.tip-success {
  background: linear-gradient(135deg, #E8FFEA 0%, #D3FFD7 100%);
  color: #00B42A;
}

.tip-icon.tip-warning {
  background: linear-gradient(135deg, #FFF7E8 0%, #FFECC8 100%);
  color: #FF7D00;
}

.tip-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tip-title {
  font-size: 14px;
  font-weight: 600;
  color: #4e5969;
}

.tip-desc {
  font-size: 12px;
  color: #86909c;
}

.layout-footer {
  background: #ffffff;
  border-top: 1px solid #e5e6eb;
  padding: 20px 32px;
}

.footer-content {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-copyright {
  font-size: 13px;
  color: #86909c;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.footer-link {
  font-size: 13px;
  color: #86909c;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #165DFF;
}

.footer-version {
  font-size: 12px;
  color: #c9cdd4;
  background: #f7f8fa;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
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

@media (max-width: 1024px) {
  .layout-header {
    padding: 0 20px;
  }

  .header-center {
    display: none;
  }

  .layout-content {
    padding: 20px;
  }

  .settings-card {
    padding: 28px 24px;
  }
}

@media (max-width: 640px) {
  .layout-header {
    padding: 0 16px;
  }

  .user-info-text {
    display: none;
  }

  .dropdown-arrow {
    display: none;
  }

  .layout-content {
    padding: 16px;
  }

  .settings-card {
    padding: 24px 20px;
    border-radius: 12px;
  }

  .settings-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .settings-title {
    font-size: 20px;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .submit-btn,
  .cancel-btn {
    width: 100%;
  }

  .security-tips {
    flex-direction: column;
    gap: 16px;
  }

  .footer-content {
    flex-direction: column;
    gap: 12px;
  }

  .footer-right {
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }
}
</style>
