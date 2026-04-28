import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, PermissionTree, Role } from '@/types'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<User | null>(null)
  const menuPermissions = ref<PermissionTree[]>([])
  const permissionCodes = ref<string[]>([])
  const userRoles = ref<Role[]>([])

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.is_super_admin ?? false)
  const needsChangePassword = computed(() => userInfo.value?.is_default_password ?? false)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUserInfo = (info: User) => {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  const setMenuPermissions = (permissions: PermissionTree[]) => {
    menuPermissions.value = permissions
    localStorage.setItem('menuPermissions', JSON.stringify(permissions))
  }

  const setPermissionCodes = (codes: string[]) => {
    permissionCodes.value = codes
    localStorage.setItem('permissionCodes', JSON.stringify(codes))
  }

  const setUserRoles = (roles: Role[]) => {
    userRoles.value = roles
    localStorage.setItem('userRoles', JSON.stringify(roles))
  }

  const hasPermission = (code: string): boolean => {
    if (isAdmin.value) {
      return true
    }
    return permissionCodes.value.includes(code)
  }

  const hasAnyPermission = (codes: string[]): boolean => {
    if (isAdmin.value) {
      return true
    }
    return codes.some(code => permissionCodes.value.includes(code))
  }

  const hasAllPermissions = (codes: string[]): boolean => {
    if (isAdmin.value) {
      return true
    }
    return codes.every(code => permissionCodes.value.includes(code))
  }

  const login = async (loginName: string, password: string) => {
    const result = await authApi.login({ login_name: loginName, password })
    setToken(result.access_token)
    setUserInfo(result.user)
    await fetchUserPermissions()
    return result
  }

  const fetchUserPermissions = async () => {
    try {
      const [menuRes, permRes, rolesRes] = await Promise.all([
        authApi.getMenuPermissions(),
        authApi.getPermissions(),
        authApi.getUserRoles(),
      ])
      
      if (menuRes.code === 200) {
        setMenuPermissions(menuRes.data)
      }
      if (permRes.code === 200) {
        setPermissionCodes(permRes.data)
      }
      if (rolesRes.code === 200) {
        setUserRoles(rolesRes.data)
      }
    } catch (error) {
      console.error('获取用户权限失败:', error)
    }
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    const result = await authApi.changePassword({
      old_password: oldPassword,
      new_password: newPassword,
    })
    
    if (userInfo.value) {
      userInfo.value.is_default_password = false
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    }
    
    return result
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    menuPermissions.value = []
    permissionCodes.value = []
    userRoles.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('menuPermissions')
    localStorage.removeItem('permissionCodes')
    localStorage.removeItem('userRoles')
  }

  const restoreFromStorage = () => {
    const storedUserInfo = localStorage.getItem('userInfo')
    if (storedUserInfo) {
      try {
        userInfo.value = JSON.parse(storedUserInfo)
      } catch {
        userInfo.value = null
      }
    }
    
    const storedMenuPermissions = localStorage.getItem('menuPermissions')
    if (storedMenuPermissions) {
      try {
        menuPermissions.value = JSON.parse(storedMenuPermissions)
      } catch {
        menuPermissions.value = []
      }
    }
    
    const storedPermissionCodes = localStorage.getItem('permissionCodes')
    if (storedPermissionCodes) {
      try {
        permissionCodes.value = JSON.parse(storedPermissionCodes)
      } catch {
        permissionCodes.value = []
      }
    }
    
    const storedUserRoles = localStorage.getItem('userRoles')
    if (storedUserRoles) {
      try {
        userRoles.value = JSON.parse(storedUserRoles)
      } catch {
        userRoles.value = []
      }
    }
  }

  return {
    token,
    userInfo,
    menuPermissions,
    permissionCodes,
    userRoles,
    isLoggedIn,
    isAdmin,
    needsChangePassword,
    setToken,
    setUserInfo,
    setMenuPermissions,
    setPermissionCodes,
    setUserRoles,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    login,
    fetchUserPermissions,
    changePassword,
    logout,
    restoreFromStorage,
  }
})