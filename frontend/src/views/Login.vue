<template>
  <div class="login-page">
    <div class="login-background">
      <div class="bg-gradient bg-gradient-1"></div>
      <div class="bg-gradient bg-gradient-2"></div>
      <div class="bg-pattern"></div>
      <div class="bg-floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
      </div>
    </div>

    <div class="login-content">
      <div class="login-left-section">
        <div class="brand-section animate-slide-up">
          <div class="logo-wrapper">
            <div class="logo-icon">
              <RobotOutlined class="logo-robot" />
            </div>
            <div class="logo-badge">
              <span>企业级</span>
            </div>
          </div>
          <h1 class="brand-title">
            智现 <span class="brand-highlight">AgentNow</span>
          </h1>
          <p class="brand-subtitle">企业智能体平台</p>
          
          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-icon">
                <ThunderboltOutlined />
              </div>
              <span>智能对话交互</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <SafetyCertificateOutlined />
              </div>
              <span>企业级安全保障</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <DashboardOutlined />
              </div>
              <span>高效协作管理</span>
            </div>
          </div>

          <div class="brand-quote">
            <blockquote>
              "让智能体成为您的数字员工，释放创造力与生产力"
            </blockquote>
          </div>
        </div>
      </div>

      <div class="login-right-section">
        <div class="login-card-wrapper animate-slide-up">
          <div class="login-card">
            <div class="card-header">
              <h2 class="card-title">欢迎登录</h2>
              <p class="card-subtitle">请使用您的企业账号登录平台</p>
            </div>

            <a-form
              ref="formRef"
              :model="formState"
              :rules="rules"
              layout="vertical"
              @finish="handleLogin"
              class="login-form"
            >
              <a-form-item class="form-item" name="phone" label="账号">
                <div class="input-wrapper">
                  <a-input
                    v-model:value="formState.phone"
                    size="large"
                    placeholder="请输入账号或手机号"
                    class="custom-input"
                  >
                    <template #prefix>
                      <UserOutlined class="input-prefix-icon" />
                    </template>
                  </a-input>
                </div>
              </a-form-item>

              <a-form-item class="form-item" name="password" label="密码">
                <div class="input-wrapper">
                  <a-input-password
                    v-model:value="formState.password"
                    size="large"
                    placeholder="请输入密码"
                    class="custom-input"
                  >
                    <template #prefix>
                      <LockOutlined class="input-prefix-icon" />
                    </template>
                  </a-input-password>
                </div>
              </a-form-item>

              <div class="form-options">
                <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
                <a-button type="link" class="forgot-link">忘记密码？</a-button>
              </div>

              <a-form-item class="form-submit">
                <a-button
                  type="primary"
                  html-type="submit"
                  class="login-btn"
                  :loading="loading"
                >
                  <template #icon v-if="!loading">
                    <LoginOutlined />
                  </template>
                  {{ loading ? '登录中...' : '登 录' }}
                </a-button>
              </a-form-item>
            </a-form>

            <div class="card-footer">
              <div class="security-hint">
                <SafetyCertificateOutlined class="security-icon" />
                <span>您的数据已通过 256 位 SSL 加密保护</span>
              </div>
            </div>
          </div>

          <div class="login-copyright">
            <p>© 2026 智现 AgentNow 企业智能体平台</p>
            <div class="copyright-links">
              <a href="#">隐私政策</a>
              <span class="separator">|</span>
              <a href="#">服务条款</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import {
  RobotOutlined,
  UserOutlined,
  LockOutlined,
  LoginOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  DashboardOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const formState = reactive({
  phone: '',
  password: '',
})

const rules: Record<string, Rule[]> = {
  phone: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const result = await userStore.login(formState.phone, formState.password)

    message.success('登录成功')

    if (result.user.is_default_password) {
      router.push({ name: 'ChangePassword' })
    } else {
      const redirect = route.query.redirect as string
      router.push(redirect || { name: 'Dashboard' })
    }
  } catch (error) {
    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.login-background {
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

.bg-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: center center;
  mask-image: radial-gradient(circle at center, black 0%, transparent 80%);
  -webkit-mask-image: radial-gradient(circle at center, black 0%, transparent 80%);
}

.bg-floating-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 15%;
  left: 10%;
  transform: rotate(15deg);
  animation: float 18s ease-in-out infinite;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  left: 5%;
  transform: rotate(-10deg);
  animation: float 20s ease-in-out infinite reverse;
}

.shape-3 {
  width: 160px;
  height: 160px;
  bottom: 20%;
  right: 8%;
  transform: rotate(25deg);
  animation: float 16s ease-in-out infinite;
}

.shape-4 {
  width: 100px;
  height: 100px;
  top: 25%;
  right: 15%;
  transform: rotate(-20deg);
  animation: float 22s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(var(--rotate, 0deg));
  }
  50% {
    transform: translateY(-20px) rotate(calc(var(--rotate, 0deg) + 5deg));
  }
}

.login-content {
  position: relative;
  z-index: 10;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  max-width: 1600px;
  margin: 0 auto;
}

.login-left-section {
  display: flex;
  align-items: center;
  padding: 48px;
  padding-left: 64px;
}

.brand-section {
  max-width: 520px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(22, 93, 255, 0.3);
}

.logo-robot {
  font-size: 36px;
  color: white;
}

.logo-badge {
  background: rgba(22, 93, 255, 0.15);
  border: 1px solid rgba(22, 93, 255, 0.3);
  border-radius: 9999px;
  padding: 4px 12px;
}

.logo-badge span {
  font-size: 12px;
  font-weight: 600;
  color: #4080FF;
  letter-spacing: 0.5px;
}

.brand-title {
  font-size: 44px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.brand-highlight {
  background: linear-gradient(135deg, #4080FF 0%, #722ed1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 40px 0;
  font-weight: 400;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 48px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-icon {
  width: 40px;
  height: 40px;
  background: rgba(22, 93, 255, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4080FF;
  font-size: 18px;
}

.feature-item span {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  font-weight: 500;
}

.brand-quote blockquote {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.8;
  margin: 0;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border-left: 3px solid rgba(22, 93, 255, 0.3);
  font-style: italic;
}

.login-right-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.login-card-wrapper {
  width: 100%;
  max-width: 440px;
}

.login-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px;
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-title {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 8px 0;
}

.card-subtitle {
  font-size: 14px;
  color: #86909c;
  margin: 0;
}

.login-form {
  animation: fadeIn 0.5s ease-out;
}

.form-item {
  margin-bottom: 20px;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  color: #4e5969;
  font-size: 14px;
}

.input-wrapper {
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-link {
  color: #165DFF;
  font-size: 13px;
  padding: 0;
  height: auto;
}

.forgot-link:hover {
  color: #4080FF;
}

.form-submit {
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.35);
  transition: all 0.25s ease;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(22, 93, 255, 0.45);
  background: linear-gradient(135deg, #4080FF 0%, #165DFF 100%);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
}

.card-footer {
  margin-top: 28px;
}

.security-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(0, 180, 42, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(0, 180, 42, 0.1);
}

.security-icon {
  color: #00B42A;
  font-size: 16px;
}

.security-hint span {
  font-size: 12px;
  color: #86909c;
}

.login-copyright {
  margin-top: 24px;
  text-align: center;
}

.login-copyright p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 8px 0;
}

.copyright-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.copyright-links a {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-decoration: none;
  transition: color 0.2s;
}

.copyright-links a:hover {
  color: rgba(255, 255, 255, 0.6);
}

.copyright-links .separator {
  color: rgba(255, 255, 255, 0.2);
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
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

@media (max-width: 1024px) {
  .login-content {
    grid-template-columns: 1fr;
  }

  .login-left-section {
    display: none;
  }

  .login-right-section {
    padding: 32px 24px;
  }

  .login-card {
    padding: 32px 24px;
  }

  .brand-title {
    font-size: 32px;
  }
}

@media (max-width: 640px) {
  .login-right-section {
    padding: 24px 16px;
  }

  .login-card {
    padding: 24px 20px;
    border-radius: 16px;
  }

  .card-title {
    font-size: 20px;
  }

  .login-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>
