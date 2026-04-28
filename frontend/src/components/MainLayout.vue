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
            <div
              v-for="menu in topLevelMenus"
              :key="menu.id"
            >
              <template v-if="!menu.children || menu.children.length === 0">
                <div
                  class="nav-menu-item"
                  :class="{ 'nav-menu-item-active': isActiveRoute(menu.path || '') }"
                  @click="handleNavigate(menu.path || '/')"
                >
                  <component :is="getIconComponent(menu.icon || '')" class="nav-icon" />
                  <span class="nav-text">{{ menu.name }}</span>
                </div>
              </template>
              <template v-else>
                <a-dropdown :trigger="['hover']" placement="bottom">
                  <div
                    class="nav-menu-item"
                    :class="{ 'nav-menu-item-active': isMenuActive(menu) }"
                  >
                    <component :is="getIconComponent(menu.icon || '')" class="nav-icon" />
                    <span class="nav-text">{{ menu.name }}</span>
                    <DownOutlined class="nav-arrow" />
                  </div>
                  <template #overlay>
                    <div class="nav-submenu">
                      <div
                        v-for="child in menu.children"
                        :key="child.id"
                        class="submenu-item"
                        :class="{ 'submenu-item-active': isActiveRoute(child.path || '') }"
                        @click="handleNavigate(child.path || '/')"
                      >
                        <div class="submenu-icon-wrapper">
                          <component :is="getIconComponent(child.icon || '')" class="submenu-icon" />
                        </div>
                        <div class="submenu-content">
                          <span class="submenu-title">{{ child.name }}</span>
                          <span class="submenu-desc">{{ getMenuDescription(child) }}</span>
                        </div>
                      </div>
                    </div>
                  </template>
                </a-dropdown>
              </template>
            </div>
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
import { computed } from 'vue'
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
  DashboardOutlined,
  ToolOutlined,
  MonitorOutlined,
  OrderedListOutlined,
  KeyOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'
import type { PermissionTree } from '@/types'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const iconMap: Record<string, unknown> = {
  'dashboard': DashboardOutlined,
  'team': TeamOutlined,
  'setting': SettingOutlined,
  'safety-certificate': SafetyCertificateOutlined,
  'robot': RobotOutlined,
  'folder-open': FolderOpenOutlined,
  'apartment': ApartmentOutlined,
  'user': UserOutlined,
  'tool': ToolOutlined,
  'monitor': MonitorOutlined,
  'list': OrderedListOutlined,
  'key': KeyOutlined,
  'file': FileTextOutlined,
  'unordered-list': UnorderedListOutlined,
}

const defaultIcon = QuestionCircleOutlined

const getIconComponent = (iconName: string) => {
  return iconMap[iconName] || defaultIcon
}

const topLevelMenus = computed<PermissionTree[]>(() => {
  return userStore.menuPermissions || []
})

const getMenuDescription = (menu: PermissionTree): string => {
  const descMap: Record<string, string> = {
    'department': '管理组织架构与层级',
    'employee': '管理员工账号与信息',
    'role:manage': '管理系统角色',
    'permission:manage': '配置系统功能与权限',
    'system:setting': '系统参数配置',
    'system:monitor': '系统运行监控',
    'agent:list': '管理智能体列表',
    'agent:config': '配置智能体参数',
    'agent:conversation': '查看对话记录',
    'knowledge:document': '管理知识库文档',
    'knowledge:setting': '知识库配置',
  }
  return descMap[menu.code] || `进入${menu.name}`
}

const isMenuActive = (menu: PermissionTree): boolean => {
  if (!menu.children || menu.children.length === 0) {
    return isActiveRoute(menu.path || '')
  }
  return menu.children.some(child => isActiveRoute(child.path || ''))
}

const handleGoHome = () => {
  router.push({ name: 'Dashboard' })
}

const isActiveRoute = (path: string) => {
  if (!path) return false
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
  padding: 0 40px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(229, 230, 235, 0.8);
  height: 68px;
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-wrapper:hover {
  background: rgba(22, 93, 255, 0.06);
  transform: translateY(-1px);
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 50%, #722ED1 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 6px 20px rgba(22, 93, 255, 0.3),
    0 2px 6px rgba(22, 93, 255, 0.15);
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
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.25) 0%, transparent 100%);
  border-radius: 12px 12px 0 0;
}

.logo-robot {
  font-size: 22px;
  color: white;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.15));
}

.logo-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
  white-space: nowrap;
}

.logo-chinese {
  font-size: 18px;
  font-weight: 700;
  color: #1d2129;
  letter-spacing: 1.5px;
  line-height: 1.2;
}

.logo-english {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: flex-start;
  padding-left: 48px;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  color: #646a73;
  position: relative;
}

.nav-menu-item:hover {
  background: rgba(22, 93, 255, 0.08);
  color: #165DFF;
}

.nav-menu-item-active {
  background: rgba(22, 93, 255, 0.12);
  color: #165DFF;
  font-weight: 500;
}

.nav-menu-item-active::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: linear-gradient(90deg, #165DFF 0%, #722ED1 100%);
  border-radius: 2px;
}

.nav-icon {
  font-size: 18px;
}

.nav-text {
  font-size: 14px;
  letter-spacing: 0.3px;
}

.nav-arrow {
  font-size: 11px;
  color: #86909c;
  transition: all 0.25s ease;
  margin-left: 2px;
}

.nav-menu-item:hover .nav-arrow {
  transform: rotate(180deg);
  color: #165DFF;
}

.nav-submenu {
  border-radius: 16px;
  box-shadow: 
    0 24px 64px rgba(0, 0, 0, 0.12),
    0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(229, 230, 235, 0.9);
  padding: 8px;
  min-width: 360px;
  backdrop-filter: blur(24px);
  background: rgba(255, 255, 255, 0.96);
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  margin: 2px 0;
}

.submenu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: linear-gradient(180deg, #165DFF 0%, #722ED1 100%);
  border-radius: 0 12px 12px 0;
  transition: all 0.3s ease;
  opacity: 0.1;
}

.submenu-item:hover {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.06) 0%, rgba(114, 46, 209, 0.03) 100%);
}

.submenu-item:hover::before {
  width: 3px;
  opacity: 1;
}

.submenu-item-active {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.1) 0%, rgba(114, 46, 209, 0.05) 100%);
}

.submenu-item-active::before {
  width: 3px;
  opacity: 1;
}

.submenu-icon-wrapper {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(247, 248, 250, 0.9) 0%, rgba(242, 243, 245, 0.9) 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.submenu-item:hover .submenu-icon-wrapper {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.12) 0%, rgba(114, 46, 209, 0.08) 100%);
  transform: scale(1.05);
}

.submenu-item-active .submenu-icon-wrapper {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.15) 0%, rgba(114, 46, 209, 0.1) 100%);
}

.submenu-icon {
  font-size: 20px;
  color: #646a73;
  transition: all 0.3s ease;
}

.submenu-item:hover .submenu-icon {
  color: #165DFF;
}

.submenu-item-active .submenu-icon {
  color: #165DFF;
}

.submenu-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.submenu-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  transition: all 0.3s ease;
}

.submenu-item:hover .submenu-title {
  color: #165DFF;
}

.submenu-item-active .submenu-title {
  color: #165DFF;
  font-weight: 600;
}

.submenu-desc {
  font-size: 12px;
  color: #86909c;
  line-height: 1.4;
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