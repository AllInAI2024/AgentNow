import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('@/views/ChangePassword.vue'),
    meta: { title: '修改密码', requiresAuth: true, requiresChangePassword: true },
  },
  {
    path: '/settings/password',
    name: 'PasswordSettings',
    component: () => import('@/views/PasswordSettings.vue'),
    meta: { title: '修改密码', requiresAuth: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '工作台', requiresAuth: true },
  },
  {
    path: '/organization/department',
    name: 'DepartmentManage',
    component: () => import('@/views/DepartmentManage.vue'),
    meta: { title: '部门管理', requiresAuth: true },
  },
  {
    path: '/organization/employee',
    name: 'EmployeeManage',
    component: () => import('@/views/EmployeeManage.vue'),
    meta: { title: '员工管理', requiresAuth: true },
  },
  {
    path: '/permission/manage',
    name: 'PermissionManage',
    component: () => import('@/views/PermissionManage.vue'),
    meta: { title: '功能点管理', requiresAuth: true },
  },
  {
    path: '/role/manage',
    name: 'RoleManage',
    component: () => import('@/views/RoleManage.vue'),
    meta: { title: '角色管理', requiresAuth: true },
  },
  {
    path: '/knowledge/document',
    name: 'KnowledgeDocument',
    component: () => import('@/views/KnowledgeDocument.vue'),
    meta: { title: '文档列表', requiresAuth: true },
  },
  {
    path: '/agents',
    name: 'MyAgents',
    component: () => import('@/views/agent/MyAgents.vue'),
    meta: { title: '我的智能体', requiresAuth: true },
  },
  {
    path: '/agents/:agentId/chat',
    name: 'AgentChat',
    component: () => import('@/views/agent/Chat.vue'),
    meta: { title: '智能体对话', requiresAuth: true },
  },
  {
    path: '/agent/list',
    redirect: '/agents',
  },
  {
    path: '/agent/conversation',
    redirect: '/agents',
  },
  {
    path: '/agent/config',
    redirect: '/agents',
  },
  {
    path: '/hermes',
    redirect: '/hermes/overview',
    meta: { title: 'Hermes 系统管理', requiresAuth: true },
    children: [
      {
        path: 'overview',
        name: 'HermesOverview',
        component: () => import('@/views/hermes/Overview.vue'),
        meta: { title: '系统概览', requiresAuth: true },
      },
      {
        path: 'profiles',
        name: 'HermesProfiles',
        component: () => import('@/views/hermes/Profiles.vue'),
        meta: { title: 'Profiles 管理', requiresAuth: true },
      },
      {
        path: 'conversations',
        name: 'HermesConversations',
        component: () => import('@/views/hermes/Conversations.vue'),
        meta: { title: '对话日志管理', requiresAuth: true },
      },
      {
        path: 'skills',
        name: 'HermesSkills',
        component: () => import('@/views/hermes/Skills.vue'),
        meta: { title: '技能管理', requiresAuth: true },
      },
      {
        path: 'mcp',
        name: 'HermesMCP',
        component: () => import('@/views/hermes/MCP.vue'),
        meta: { title: 'MCP 服务', requiresAuth: true },
      },
      {
        path: 'tools',
        name: 'HermesTools',
        component: () => import('@/views/hermes/Tools.vue'),
        meta: { title: '工具集', requiresAuth: true },
      },
      {
        path: 'memory',
        name: 'HermesMemory',
        component: () => import('@/views/hermes/Memory.vue'),
        meta: { title: '记忆系统', requiresAuth: true },
      },
      {
        path: 'config',
        name: 'HermesConfig',
        component: () => import('@/views/hermes/Config.vue'),
        meta: { title: '配置管理', requiresAuth: true },
      },
      {
        path: 'knowledge',
        name: 'HermesKnowledge',
        component: () => import('@/views/hermes/Knowledge.vue'),
        meta: { title: '知识库管理', requiresAuth: true },
      },
      {
        path: 'audit',
        name: 'HermesAudit',
        component: () => import('@/views/hermes/Audit.vue'),
        meta: { title: '操作审计', requiresAuth: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || '智现 AgentNow'} - 企业智能体平台`
  
  const userStore = useUserStore()
  
  if (!userStore.userInfo && userStore.isLoggedIn) {
    userStore.restoreFromStorage()
  }
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  if (to.name === 'Login' && userStore.isLoggedIn) {
    if (userStore.needsChangePassword) {
      next({ name: 'ChangePassword' })
    } else {
      next({ name: 'Dashboard' })
    }
    return
  }
  
  if (userStore.isLoggedIn && userStore.needsChangePassword && to.name !== 'ChangePassword') {
    next({ name: 'ChangePassword' })
    return
  }
  
  if (userStore.isLoggedIn && !userStore.needsChangePassword && to.meta.requiresChangePassword) {
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})

export default router
