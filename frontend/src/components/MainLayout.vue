<template>
  <div class="layout-page">
    <a-layout class="layout-container">
      <a-layout-header class="layout-header">
        <div class="header-left">
          <div class="logo-wrapper" @click="handleGoHome">
            <div class="logo-icon">
              <RobotOutlined class="logo-robot" />
            </div>
            <div class="logo-brand">
              <span class="logo-chinese">智现</span>
              <span class="logo-english">AgentNow</span>
            </div>
          </div>
        </div>

        <div class="header-center">
          <div class="nav-menu">
            <a-dropdown :trigger="['hover']" placement="bottom">
              <div class="nav-menu-item" :class="{ 'nav-menu-item-active': isActiveRoute('/organization') }">
                <TeamOutlined class="nav-icon" />
                <span>组织管理</span>
                <DownOutlined class="nav-arrow" />
              </div>
              <template #overlay>
                <a-menu class="nav-submenu">
                  <a-menu-item 
                    key="/organization/department" 
                    @click="handleNavigate('/organization/department')"
                    :class="{ 'ant-menu-item-selected': isActiveRoute('/organization/department') }"
                  >
                    <ApartmentOutlined class="submenu-icon" />
                    <span>部门管理</span>
                  </a-menu-item>
                  <a-menu-item 
                    key="/organization/employee" 
                    @click="handleNavigate('/organization/employee')"
                    :class="{ 'ant-menu-item-selected': isActiveRoute('/organization/employee') }"
                  >
                    <UserOutlined class="submenu-icon" />
                    <span>员工管理</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>

            <a-dropdown :trigger="['hover']" placement="bottom">
              <div class="nav-menu-item" :class="{ 'nav-menu-item-active': isActiveRoute('/role') }">
                <SafetyCertificateOutlined class="nav-icon" />
                <span>角色权限</span>
                <DownOutlined class="nav-arrow" />
              </div>
              <template #overlay>
                <a-menu class="nav-submenu">
                  <a-menu-item 
                    key="/permission/manage" 
                    @click="handleNavigate('/permission/manage')"
                    :class="{ 'ant-menu-item-selected': isActiveRoute('/permission/manage') }"
                  >
                    <UnorderedListOutlined class="submenu-icon" />
                    <span>功能点管理</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
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
                  <a-menu-item key="profile" @click="handleProfile">
                    <UserOutlined class="menu-icon" />
                    <span>个人中心</span>
                  </a-menu-item>
                  <a-menu-item key="changePassword" @click="handleChangePassword">
                    <LockOutlined class="menu-icon" />
                    <span>修改密码</span>
                  </a-menu-item>
                  <a-menu-item key="settings" @click="handleSettings">
                    <SettingOutlined class="menu-icon" />
                    <span>账户设置</span>
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
        <slot></slot>
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
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  RobotOutlined,
  DownOutlined,
  UserOutlined,
  LockOutlined,
  LogoutOutlined,
  BellOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ApartmentOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const handleGoHome = () => {
  router.push({ name: 'Dashboard' })
}

const isActiveRoute = (path: string) => {
  return router.currentRoute.value.path.startsWith(path)
}

const handleNavigate = (path: string) => {
  router.push(path)
}

const handleProfile = () => {
  message.info('个人中心功能开发中...')
}

const handleChangePassword = () => {
  router.push({ name: 'PasswordSettings' })
}

const handleSettings = () => {
  message.info('账户设置功能开发中...')
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
.layout-page {
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
  gap: 16px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.logo-wrapper:hover {
  background: rgba(22, 93, 255, 0.06);
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 50%, #722ED1 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 8px 24px rgba(22, 93, 255, 0.35),
    0 2px 8px rgba(22, 93, 255, 0.2);
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, transparent 100%);
  border-radius: 14px 14px 0 0;
}

.logo-robot {
  font-size: 26px;
  color: white;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.logo-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
  white-space: nowrap;
}

.logo-chinese {
  font-size: 20px;
  font-weight: 700;
  color: #1d2129;
  letter-spacing: 2px;
  line-height: 1.2;
}

.logo-english {
  font-size: 13px;
  font-weight: 600;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
  line-height: 1.2;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: flex-start;
  padding-left: 40px;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #4e5969;
}

.nav-menu-item:hover {
  background: rgba(22, 93, 255, 0.08);
  color: #165DFF;
}

.nav-menu-item-active {
  background: rgba(22, 93, 255, 0.1);
  color: #165DFF;
  font-weight: 500;
}

.nav-icon {
  font-size: 16px;
}

.nav-arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.nav-menu-item:hover .nav-arrow {
  transform: rotate(180deg);
}

:deep(.nav-submenu) {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e6eb;
  padding: 8px;
  min-width: 260px;
}

:deep(.nav-submenu .ant-menu-item) {
  border-radius: 8px;
  margin: 4px 0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s ease;
}

:deep(.nav-submenu .ant-menu-item:hover) {
  background: rgba(22, 93, 255, 0.06);
}

:deep(.nav-submenu .ant-menu-item-selected) {
  background: rgba(22, 93, 255, 0.1);
  color: #165DFF;
}

.submenu-icon {
  font-size: 16px;
  color: #86909c;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
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
  max-width: 1440px;
  margin: 0 auto;
  width: 100%;
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

  .footer-content {
    flex-direction: column;
    gap: 12px;
  }

  .footer-right {
    gap: 16px;
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

  .footer-content {
    text-align: center;
  }

  .footer-right {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>