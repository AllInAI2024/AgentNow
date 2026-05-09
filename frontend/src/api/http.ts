import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'

const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const debugEnabled = () => {
  try {
    return localStorage.getItem('AGENT_DEBUG') === '1'
  } catch {
    return false
  }
}

const pushDebug = (type: string, data?: unknown) => {
  if (!debugEnabled()) return
  try {
    const raw = sessionStorage.getItem('AGENT_DEBUG_HTTP') || '[]'
    const items = JSON.parse(raw) as Array<{ ts: string; type: string; data?: unknown }>
    items.push({ ts: new Date().toISOString(), type, data })
    const trimmed = items.length > 120 ? items.slice(-120) : items
    sessionStorage.setItem('AGENT_DEBUG_HTTP', JSON.stringify(trimmed))
    ;(window as any).__agentDebugHttp = trimmed
  } catch {}
}

service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    const token = userStore.token
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    pushDebug('http_request', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
    })
    
    return config
  },
  (error) => {
    pushDebug('http_request_error', { message: String(error?.message || error) })
    return Promise.reject(error)
  }
)

const extractErrorMessage = (data: unknown): string => {
  if (typeof data === 'string') {
    return data
  }
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (obj.detail) {
      if (Array.isArray(obj.detail) && obj.detail.length > 0) {
        const firstError = obj.detail[0]
        if (firstError && typeof firstError === 'object' && 'msg' in firstError) {
          return (firstError as { msg: string }).msg
        }
        return String(firstError)
      }
      return String(obj.detail)
    }
    if (obj.message) {
      return String(obj.message)
    }
  }
  return ''
}

service.interceptors.response.use(
  (response: AxiosResponse) => {
    pushDebug('http_response', {
      url: response.config?.url,
      status: response.status,
    })
    return response.data
  },
  (error) => {
    const { response, config } = error
    
    if (response) {
      const isLoginRequest = config?.url?.includes('/auth/login')
      pushDebug('http_error', {
        url: config?.url,
        status: response.status,
        detail: extractErrorMessage(response.data),
      })
      
      switch (response.status) {
        case 401:
          const errorMsg401 = extractErrorMessage(response.data) || '登录已过期，请重新登录'
          message.error(errorMsg401)
          const userStore = useUserStore()
          if (userStore.isLoggedIn) {
            userStore.logout()
            pushDebug('redirect_login', { reason: '401', url: config?.url })
            window.location.href = '/login'
          }
          break
        case 403:
          message.error('没有权限访问')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 422:
          if (isLoginRequest) {
            message.error('账号或密码错误')
          } else {
            const errorMsg422 = extractErrorMessage(response.data) || '参数验证失败'
            message.error(errorMsg422)
          }
          break
        case 500:
          message.error('服务器错误')
          break
        default:
          const errorMsgDefault = extractErrorMessage(response.data) || '请求失败'
          message.error(errorMsgDefault)
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default service
