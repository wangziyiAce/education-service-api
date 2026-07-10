/**
 * 路由守卫组件。
 *
 * 职责：
 * 1. 检查用户是否已登录（有无 token）
 * 2. 未登录 → 重定向到 /login
 * 3. 已登录但无用户信息 → 尝试调用 /auth/me 获取
 * 4. 加载中 → 显示 LoadingState
 *
 * 注意：不将 children 包裹在 <></> Fragment 中，
 * 避免 React Router 在路由切换时出现 insertBefore 错误。
 */

import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'
import { getMe } from '@/api/auth'
import LoadingState from '@/components/shared/LoadingState'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, user, logout } = useAuthStore()
  const [loading, setLoading] = useState(!user && !!token)
  const location = useLocation()

  useEffect(() => {
    // 有 token 但没有 user 信息：尝试获取用户信息
    if (token && !user) {
      setLoading(true)
      getMe()
        .then((res) => {
          useAuthStore.setState({ user: res.data })
        })
        .catch(() => {
          logout()
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [token, user, logout])

  // 未登录 → 跳转登录页
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 正在获取用户信息
  if (loading) {
    return <LoadingState text="正在加载..." />
  }

  // 直接返回 children，不包裹 Fragment
  return children
}
