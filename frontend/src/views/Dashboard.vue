<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <div class="layout-logo">
        <RobotOutlined class="layout-logo-icon" />
        <span class="layout-logo-text">智现 AgentNow</span>
      </div>
      <div class="user-info">
        <a-dropdown :trigger="['click']" @visibleChange="handleDropdownVisibleChange">
          <div class="user-dropdown-trigger">
            <a-avatar class="user-avatar" :size="36">
              {{ userStore.userInfo?.username?.charAt(0) }}
            </a-avatar>
            <span class="user-name">{{ userStore.userInfo?.username }}</span>
            <DownOutlined :style="{ fontSize: '12px', color: '#8c8c8c', marginLeft: '4px' }" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile" @click="handleProfile">
                <UserOutlined />
                <span>个人中心</span>
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
      <div class="welcome-section">
        <div class="welcome-content">
          <h1 class="welcome-title">
            欢迎回来，{{ userStore.userInfo?.username }}
          </h1>
          <p class="welcome-subtitle">
            智现 AgentNow 企业智能体平台，让智能体成为您的数字员工
          </p>
        </div>
        <div class="welcome-icon">
          <RocketOutlined :style="{ fontSize: '64px', color: '#1890ff' }" />
        </div>
      </div>

      <div class="stats-section">
        <a-row :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card class="stat-card" hoverable>
              <div class="stat-content">
                <div class="stat-info">
                  <div class="stat-value">{{ stats.conversations }}</div>
                  <div class="stat-label">对话次数</div>
                </div>
                <div class="stat-icon bg-blue">
                  <MessageOutlined />
                </div>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card class="stat-card" hoverable>
              <div class="stat-content">
                <div class="stat-info">
                  <div class="stat-value">{{ stats.documents }}</div>
                  <div class="stat-label">知识文档</div>
                </div>
                <div class="stat-icon bg-green">
                  <FileTextOutlined />
                </div>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card class="stat-card" hoverable>
              <div class="stat-content">
                <div class="stat-info">
                  <div class="stat-value">{{ stats.agents }}</div>
                  <div class="stat-label">智能体数量</div>
                </div>
                <div class="stat-icon bg-purple">
                  <RobotOutlined />
                </div>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card class="stat-card" hoverable>
              <div class="stat-content">
                <div class="stat-info">
                  <div class="stat-value">{{ stats.activeUsers }}</div>
                  <div class="stat-label">活跃用户</div>
                </div>
                <div class="stat-icon bg-orange">
                  <TeamOutlined />
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </div>

      <div class="features-section">
        <h2 class="section-title">快速入口</h2>
        <a-row :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :lg="8">
            <a-card class="feature-card" hoverable @click="handleStartChat">
              <div class="feature-icon bg-chat">
                <WechatOutlined />
              </div>
              <h3 class="feature-title">智能对话</h3>
              <p class="feature-desc">与智能体进行自然语言对话，获取专业解答</p>
              <a-tag color="blue">即将推出</a-tag>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="8">
            <a-card class="feature-card" hoverable @click="handleKnowledge">
              <div class="feature-icon bg-knowledge">
                <DatabaseOutlined />
              </div>
              <h3 class="feature-title">知识库管理</h3>
              <p class="feature-desc">上传和管理企业知识文档，构建智能知识大脑</p>
              <a-tag color="green">即将推出</a-tag>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="8">
            <a-card class="feature-card" hoverable @click="handleAgents">
              <div class="feature-icon bg-agent">
                <AppstoreOutlined />
              </div>
              <h3 class="feature-title">智能体管理</h3>
              <p class="feature-desc">为不同岗位配置专属智能体，提升工作效率</p>
              <a-tag color="purple">即将推出</a-tag>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </a-layout-content>

    <a-layout-footer class="layout-footer">
      <span>© 2026 智现 AgentNow 企业智能体平台</span>
    </a-layout-footer>
  </a-layout>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  RobotOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  RocketOutlined,
  MessageOutlined,
  FileTextOutlined,
  TeamOutlined,
  WechatOutlined,
  DatabaseOutlined,
  AppstoreOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const stats = reactive({
  conversations: 0,
  documents: 0,
  agents: 0,
  activeUsers: 0,
})

const handleDropdownVisibleChange = (_visible: boolean) => {}

const handleProfile = () => {
  message.info('个人中心功能开发中...')
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

const handleStartChat = () => {
  message.info('智能对话功能开发中...')
}

const handleKnowledge = () => {
  message.info('知识库管理功能开发中...')
}

const handleAgents = () => {
  message.info('智能体管理功能开发中...')
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

.layout-footer {
  text-align: center;
  color: #8c8c8c;
  font-size: 12px;
  padding: 24px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border-radius: 16px;
  margin-bottom: 24px;
}

.welcome-content {
  flex: 1;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.welcome-icon {
  padding-left: 24px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.bg-blue {
  background: linear-gradient(135deg, #1890ff 0%, #69c0ff 100%);
}

.stat-icon.bg-green {
  background: linear-gradient(135deg, #52c41a 0%, #95de64 100%);
}

.stat-icon.bg-purple {
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
}

.stat-icon.bg-orange {
  background: linear-gradient(135deg, #fa8c16 0%, #ffc069 100%);
}

.features-section {
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 16px 0;
}

.feature-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  text-align: center;
  padding: 16px;
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
  margin: 0 auto 16px;
}

.feature-icon.bg-chat {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
}

.feature-icon.bg-knowledge {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
}

.feature-icon.bg-agent {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

.feature-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.feature-desc {
  font-size: 13px;
  color: #8c8c8c;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }

  .layout-content {
    margin: 16px;
  }

  .welcome-section {
    flex-direction: column;
    text-align: center;
    padding: 24px;
  }

  .welcome-icon {
    padding-left: 0;
    margin-top: 16px;
  }

  .welcome-title {
    font-size: 22px;
  }
}
</style>
