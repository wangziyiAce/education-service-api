import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,
})

// 请求拦截器：注入 JWT Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一解包 {code, message, data}
request.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    // 后端不同模块返回的成功码不同：auth 用 0，CRM 用 200
    if (code === 0 || code === 200) {
      return data
    }
    // 业务错误码处理
    switch (code) {
      case 40101:
      case 40102:
      case 40103:
        localStorage.removeItem('access_token')
        window.location.href = '/login'
        break
      case 40301:
        ElMessage.error(message || '服务令牌校验失败')
        break
      case 40401:
      case 40402:
        ElMessage.error(message || '资源不存在')
        break
      default:
        ElMessage.error(message || '请求失败')
    }
    return Promise.reject({ code, message })
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      ElMessage.error('无权限访问')
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器内部错误')
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else if (!error.response) {
      ElMessage.error('网络异常，请检查连接')
    }
    return Promise.reject(error)
  }
)

export default request
