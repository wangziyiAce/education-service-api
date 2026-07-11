/**
 * Axios API Client 统一封装。
 *
 * 职责：
 * 1. 统一 baseURL 和超时配置
 * 2. 请求拦截器：自动注入 JWT Bearer Token
 * 3. 响应拦截器：关键错误（401/403）立即提示；
 *    服务端错误（500/网络异常）做节流，避免批量请求重复弹窗
 * 4. 各页面的 TanStack Query 自行通过 ErrorState 组件展示错误细节
 *
 * 后端 API 前缀：/api/v1（由环境变量 VITE_API_BASE_URL 配置）
 * 开发期通过 Vite proxy 转发到 FastAPI（localhost:8000）
 */

import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { toast } from 'sonner'

/** 从 localStorage 读取 JWT Token */
function getToken(): string | null {
  try {
    const stored = localStorage.getItem('auth-storage')
    if (!stored) return null
    const parsed = JSON.parse(stored)
    return parsed?.state?.token ?? null
  } catch {
    return null
  }
}

// ---- 节流：同类型错误 10 秒内只弹一次 toast ----
const _lastToastTime: Record<string, number> = {}

function _throttledToast(key: string, message: string, type: 'error' | 'warning' = 'error') {
  const now = Date.now()
  const last = _lastToastTime[key] || 0
  if (now - last > 10_000) {
    _lastToastTime[key] = now
    if (type === 'warning') {
      toast.warning(message)
    } else {
      toast.error(message)
    }
  }
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

/** 请求拦截器：注入 JWT Token */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/** 响应拦截器：关键错误立即提示，服务端错误做节流 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    // 网络不通（后端完全没响应）
    if (!error.response) {
      _throttledToast('network', '无法连接到服务器，请确认后端已启动', 'error')
      return Promise.reject(error)
    }

    const { status } = error.response
    const detail = error.response.data?.detail

    switch (status) {
      // 401：Token 过期或无效 → 必须立即提示并跳转登录
      case 401: {
        localStorage.removeItem('auth-storage')
        toast.error('登录已过期，请重新登录')
        const isLoginPage = window.location.pathname === '/login'
        if (!isLoginPage) {
          setTimeout(() => {
            window.location.href = '/login'
          }, 1000)
        }
        break
      }

      // 403：权限不足 → 立即提示
      case 403:
        toast.error(detail || '无权限访问')
        break

      // 400 / 422：参数校验失败 → 立即提示（通常是表单提交时触发）
      case 400:
      case 422:
        toast.warning(detail || '请求参数有误')
        break

      // 500：服务器内部错误 → 节流（多组件同时请求时只弹一次）
      case 500:
        _throttledToast('server-500', '服务器内部错误，请稍后重试', 'error')
        break

      // 其他错误码 → 节流
      default:
        _throttledToast(`http-${status}`, detail || `请求失败 (${status})`, 'error')
    }

    return Promise.reject(error)
  }
)

export { apiClient }
export default apiClient
