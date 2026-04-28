import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const needsChangePassword = computed(() => userInfo.value?.is_default_password ?? false)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUserInfo = (info: User) => {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  const login = async (phone: string, password: string) => {
    const result = await authApi.login({ phone, password })
    setToken(result.access_token)
    setUserInfo(result.user)
    return result
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
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
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
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    needsChangePassword,
    setToken,
    setUserInfo,
    login,
    changePassword,
    logout,
    restoreFromStorage,
  }
})
