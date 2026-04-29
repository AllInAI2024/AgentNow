<template>
  <MainLayout>
    <div class="dashboard-content">
      <div class="welcome-section animate-slide-up">
        <div class="welcome-content">
          <div class="welcome-time">
            <span class="time-greeting">{{ getGreeting() }}</span>
            <span class="time-divider">·</span>
            <span class="time-date">{{ getCurrentDate() }}</span>
          </div>
          <h1 class="welcome-title">
            欢迎回来，{{ userStore.userInfo?.username }}
            <span class="welcome-wave">👋</span>
          </h1>
          <p class="welcome-subtitle">
            智现 AgentNow 企业智能体平台，让智能体成为您的数字员工
          </p>
        </div>
        <div class="welcome-visual">
          <div class="visual-blob blob-1"></div>
          <div class="visual-blob blob-2"></div>
          <div class="visual-icon">
            <RocketOutlined class="rocket-icon" />
          </div>
        </div>
      </div>

      <div class="stats-section animate-slide-up" style="animation-delay: 0.1s;">
        <div class="section-header">
          <h2 class="section-title">数据概览</h2>
          <a-button type="link" class="section-more">
            查看详情 <ArrowRightOutlined />
          </a-button>
        </div>
        <a-row :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-card stat-card-primary hover-lift">
              <div class="stat-card-inner">
                <div class="stat-header">
                  <div class="stat-icon-wrapper">
                    <MessageOutlined class="stat-icon" />
                  </div>
                  <a-tag color="blue" class="stat-trend">
                    <ArrowUpOutlined /> +12%
                  </a-tag>
                </div>
                <div class="stat-body">
                  <div class="stat-value">{{ stats.conversations }}</div>
                  <div class="stat-label">对话次数</div>
                </div>
                <div class="stat-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: stats.conversations > 0 ? '65%' : '0%' }"></div>
                  </div>
                  <span class="progress-text">本周目标 65%</span>
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-card stat-card-success hover-lift">
              <div class="stat-card-inner">
                <div class="stat-header">
                  <div class="stat-icon-wrapper">
                    <FileTextOutlined class="stat-icon" />
                  </div>
                  <a-tag color="green" class="stat-trend">
                    <ArrowUpOutlined /> +8%
                  </a-tag>
                </div>
                <div class="stat-body">
                  <div class="stat-value">{{ stats.documents }}</div>
                  <div class="stat-label">知识文档</div>
                </div>
                <div class="stat-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: stats.documents > 0 ? '42%' : '0%' }"></div>
                  </div>
                  <span class="progress-text">新增文档 3 篇</span>
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-card stat-card-purple hover-lift">
              <div class="stat-card-inner">
                <div class="stat-header">
                  <div class="stat-icon-wrapper">
                    <RobotOutlined class="stat-icon" />
                  </div>
                  <a-tag color="purple" class="stat-trend">
                    <ArrowUpOutlined /> +5%
                  </a-tag>
                </div>
                <div class="stat-body">
                  <div class="stat-value">{{ stats.agents }}</div>
                  <div class="stat-label">智能体数量</div>
                </div>
                <div class="stat-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: stats.agents > 0 ? '78%' : '0%' }"></div>
                  </div>
                  <span class="progress-text">在线智能体 2 个</span>
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-card stat-card-orange hover-lift">
              <div class="stat-card-inner">
                <div class="stat-header">
                  <div class="stat-icon-wrapper">
                    <TeamOutlined class="stat-icon" />
                  </div>
                  <a-tag color="orange" class="stat-trend">
                    <ArrowUpOutlined /> +15%
                  </a-tag>
                </div>
                <div class="stat-body">
                  <div class="stat-value">{{ stats.activeUsers }}</div>
                  <div class="stat-label">活跃用户</div>
                </div>
                <div class="stat-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: stats.activeUsers > 0 ? '55%' : '0%' }"></div>
                  </div>
                  <span class="progress-text">今日活跃 8 人</span>
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <div class="features-section animate-slide-up" style="animation-delay: 0.2s;">
        <div class="section-header">
          <h2 class="section-title">快速入口</h2>
          <p class="section-desc">点击下方卡片快速开始您的工作</p>
        </div>
        <a-row :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :lg="8">
            <div class="feature-card card-hover-lift" @click="handleStartChat">
              <div class="feature-card-inner">
                <div class="feature-icon-wrapper bg-gradient-chat">
                  <WechatOutlined class="feature-icon" />
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">智能对话</h3>
                  <p class="feature-desc">与智能体进行自然语言对话，获取专业解答</p>
                  <div class="feature-tags">
                    <a-tag color="blue" class="feature-tag">AI 驱动</a-tag>
                    <a-tag color="default" class="feature-tag-coming">即将推出</a-tag>
                  </div>
                </div>
                <div class="feature-arrow">
                  <RightOutlined class="arrow-icon" />
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="8">
            <div class="feature-card card-hover-lift" @click="handleKnowledge">
              <div class="feature-card-inner">
                <div class="feature-icon-wrapper bg-gradient-knowledge">
                  <DatabaseOutlined class="feature-icon" />
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">知识库管理</h3>
                  <p class="feature-desc">上传和管理企业知识文档，构建智能知识大脑</p>
                  <div class="feature-tags">
                    <a-tag color="green" class="feature-tag">RAG 技术</a-tag>
                    <a-tag color="default" class="feature-tag-coming">即将推出</a-tag>
                  </div>
                </div>
                <div class="feature-arrow">
                  <RightOutlined class="arrow-icon" />
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="8">
            <div class="feature-card card-hover-lift" @click="handleAgents">
              <div class="feature-card-inner">
                <div class="feature-icon-wrapper bg-gradient-agent">
                  <AppstoreOutlined class="feature-icon" />
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">智能体管理</h3>
                  <p class="feature-desc">为不同岗位配置专属智能体，提升工作效率</p>
                  <div class="feature-tags">
                    <a-tag color="purple" class="feature-tag">可定制</a-tag>
                    <a-tag color="default" class="feature-tag-coming">即将推出</a-tag>
                  </div>
                </div>
                <div class="feature-arrow">
                  <RightOutlined class="arrow-icon" />
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <div class="recent-section animate-slide-up" style="animation-delay: 0.3s;">
        <div class="section-header">
          <h2 class="section-title">最近活动</h2>
          <a-button type="link" class="section-more">
            查看全部 <ArrowRightOutlined />
          </a-button>
        </div>
        <div class="recent-card">
          <div class="recent-empty">
            <div class="empty-icon">
              <InboxOutlined class="inbox-icon" />
            </div>
            <h3 class="empty-title">暂无活动记录</h3>
            <p class="empty-desc">开始使用平台后，您的活动记录将显示在这里</p>
            <a-button type="primary" @click="handleStartChat">
              开始探索
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  RocketOutlined,
  MessageOutlined,
  FileTextOutlined,
  TeamOutlined,
  WechatOutlined,
  DatabaseOutlined,
  AppstoreOutlined,
  ArrowRightOutlined,
  ArrowUpOutlined,
  RightOutlined,
  InboxOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/components/MainLayout.vue'

const userStore = useUserStore()

const stats = reactive({
  conversations: 0,
  documents: 0,
  agents: 0,
  activeUsers: 0,
})

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 17) return '下午好'
  if (hour < 19) return '傍晚好'
  return '晚上好'
}

const getCurrentDate = () => {
  const now = new Date()
  const month = now.getMonth() + 1
  const day = now.getDate()
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const weekday = weekdays[now.getDay()]
  return `${month}月${day}日 ${weekday}`
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
.dashboard-content {
  width: 100%;
}

.welcome-section {
  position: relative;
  overflow: hidden;
  padding: 32px 40px;
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 50%, #722ed1 100%);
  border-radius: 20px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome-content {
  position: relative;
  z-index: 2;
}

.welcome-time {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.time-greeting {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.time-divider {
  color: rgba(255, 255, 255, 0.4);
}

.time-date {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  line-height: 1.3;
  display: flex;
  align-items: center;
  gap: 8px;
}

.welcome-wave {
  font-size: 24px;
  animation: wave 2s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(15deg); }
  75% { transform: rotate(-15deg); }
}

.welcome-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  line-height: 1.6;
}

.welcome-visual {
  position: relative;
  width: 200px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(20px);
}

.blob-1 {
  width: 120px;
  height: 120px;
  background: rgba(255, 255, 255, 0.15);
  right: -20px;
  top: -10px;
  animation: float 4s ease-in-out infinite;
}

.blob-2 {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.1);
  left: 0;
  bottom: 0;
  animation: float 5s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-10px) scale(1.05); }
}

.visual-icon {
  position: relative;
  z-index: 2;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.rocket-icon {
  font-size: 40px;
  color: white;
}

.stats-section,
.features-section,
.recent-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1d2129;
  margin: 0;
}

.section-desc {
  font-size: 14px;
  color: #86909c;
  margin: 0;
}

.section-more {
  font-size: 13px;
  color: #165DFF;
  padding: 0;
  height: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 16px 16px 0 0;
}

.stat-card-primary::before { background: linear-gradient(90deg, #165DFF, #4080FF); }
.stat-card-success::before { background: linear-gradient(90deg, #00B42A, #23C343); }
.stat-card-purple::before { background: linear-gradient(90deg, #722ed1, #9254de); }
.stat-card-orange::before { background: linear-gradient(90deg, #FF7D00, #FF9A2E); }

.stat-card-inner {
  padding: 24px;
}

.stat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card-primary .stat-icon-wrapper { background: linear-gradient(135deg, #E8F3FF 0%, #D0E8FF 100%); }
.stat-card-success .stat-icon-wrapper { background: linear-gradient(135deg, #E8FFEA 0%, #D3FFD7 100%); }
.stat-card-purple .stat-icon-wrapper { background: linear-gradient(135deg, #F3E8FF 0%, #E8D5FF 100%); }
.stat-card-orange .stat-icon-wrapper { background: linear-gradient(135deg, #FFF7E8 0%, #FFE8C8 100%); }

.stat-icon {
  font-size: 24px;
}

.stat-card-primary .stat-icon { color: #165DFF; }
.stat-card-success .stat-icon { color: #00B42A; }
.stat-card-purple .stat-icon { color: #722ed1; }
.stat-card-orange .stat-icon { color: #FF7D00; }

.stat-trend {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-body {
  margin-bottom: 16px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 4px;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
  font-weight: 500;
}

.stat-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #f2f3f5;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.stat-card-primary .progress-fill { background: linear-gradient(90deg, #165DFF, #4080FF); }
.stat-card-success .progress-fill { background: linear-gradient(90deg, #00B42A, #23C343); }
.stat-card-purple .progress-fill { background: linear-gradient(90deg, #722ed1, #9254de); }
.stat-card-orange .progress-fill { background: linear-gradient(90deg, #FF7D00, #FF9A2E); }

.progress-text {
  font-size: 12px;
  color: #86909c;
}

.hover-lift {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

.feature-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid #e5e6eb;
  transition: all 0.3s ease;
}

.card-hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
  border-color: rgba(22, 93, 255, 0.3);
}

.feature-card-inner {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.2);
}

.bg-gradient-chat { background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%); }
.bg-gradient-knowledge { background: linear-gradient(135deg, #00B42A 0%, #23C343 100%); }
.bg-gradient-agent { background: linear-gradient(135deg, #722ed1 0%, #9254de 100%); }

.feature-icon {
  font-size: 28px;
  color: white;
}

.feature-content {
  flex: 1;
}

.feature-title {
  font-size: 16px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 8px 0;
  transition: color 0.2s ease;
}

.feature-card:hover .feature-title {
  color: #165DFF;
}

.feature-desc {
  font-size: 13px;
  color: #86909c;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.feature-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.feature-tag {
  border: none;
  font-weight: 500;
  padding: 2px 8px;
  font-size: 12px;
}

.feature-tag-coming {
  background: #f7f8fa;
  color: #86909c;
  border: none;
  font-size: 12px;
  padding: 2px 8px;
}

.feature-arrow {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f7f8fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  transition: all 0.3s ease;
}

.feature-card:hover .feature-arrow {
  background: #165DFF;
}

.arrow-icon {
  font-size: 14px;
  color: #86909c;
  transition: transform 0.3s ease, color 0.3s ease;
}

.feature-card:hover .arrow-icon {
  color: white;
  transform: translateX(2px);
}

.recent-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e6eb;
  padding: 48px;
  text-align: center;
}

.recent-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #f7f8fa 0%, #f2f3f5 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.inbox-icon {
  font-size: 36px;
  color: #c9cdd4;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}

.empty-desc {
  font-size: 14px;
  color: #86909c;
  margin: 0 0 8px 0;
  max-width: 320px;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out forwards;
  opacity: 0;
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
  .welcome-section {
    padding: 24px;
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .welcome-visual {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .welcome-section {
    padding: 20px;
    border-radius: 16px;
  }

  .welcome-title {
    font-size: 22px;
  }

  .stat-value {
    font-size: 28px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>