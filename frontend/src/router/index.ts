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
    path: '/permission/manage',
    name: 'PermissionManage',
    component: () => import('@/views/PermissionManage.vue'),
    meta: { title: '功能点管理', requiresAuth: true },
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
