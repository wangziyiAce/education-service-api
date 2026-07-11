/**
 * 登录页面。
 *
 * 职责：
 * 1. 展示品牌 Logo 和产品名称"粤教智服"
 * 2. 提供用户名/密码登录表单
 * 3. 表单校验（React Hook Form + Zod）
 * 4. 登录 Loading、错误提示、防重复提交
 * 5. 演示账号说明
 * 6. 登录成功后跳转到 /dashboard
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, Navigate } from 'react-router-dom'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useAuthStore } from '@/stores/auth-store'
import type { LoginRequest } from '@/types/auth'
import { getDefaultRoute } from '@/lib/role-navigation'

/** 登录表单校验 Schema */
const loginSchema = z.object({
  username: z.string().min(1, '请输入用户名'),
  password: z.string().min(1, '请输入密码'),
})

type LoginFormData = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, login } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  })

  // 已登录 → 直接跳转
  if (isAuthenticated) {
    return <Navigate to={getDefaultRoute(useAuthStore.getState().user?.role_code)} replace />
  }

  const onSubmit = async (data: LoginFormData) => {
    setError(null)
    setIsSubmitting(true)
    try {
      await login(data as LoginRequest)
      navigate(getDefaultRoute(useAuthStore.getState().user?.role_code), { replace: true })
    } catch (err: unknown) {
      // API Client 拦截器已处理 toast 提示，这里设置表单级错误
      const axiosError = err as { response?: { data?: { detail?: string }; status?: number } }
      if (axiosError?.response?.status === 401) {
        setError('用户名或密码错误')
      } else if (axiosError?.response?.status === 0 || !axiosError?.response) {
        setError('无法连接到服务器，请检查网络或后端是否启动')
      } else {
        setError(axiosError?.response?.data?.detail || '登录失败，请稍后重试')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-950 via-brand-900 to-slate-900 p-4">
      <div className="w-full max-w-md">
        {/* 品牌标识 */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
            <span className="text-2xl font-bold text-white">粤</span>
          </div>
          <h1 className="mt-4 text-2xl font-bold text-white">粤教智服</h1>
          <p className="mt-1 text-sm text-white/60">国际教育智能服务平台</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>登录</CardTitle>
            <CardDescription>使用您的账号登录系统</CardDescription>
          </CardHeader>
          <CardContent>
            {/* 错误提示 */}
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* 用户名 */}
              <div className="space-y-2">
                <Label htmlFor="username">用户名</Label>
                <Input
                  id="username"
                  placeholder="请输入用户名"
                  autoComplete="username"
                  disabled={isSubmitting}
                  {...register('username')}
                />
                {errors.username && (
                  <p className="text-xs text-destructive">{errors.username.message}</p>
                )}
              </div>

              {/* 密码 */}
              <div className="space-y-2">
                <Label htmlFor="password">密码</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="请输入密码"
                    autoComplete="current-password"
                    disabled={isSubmitting}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              {/* 提交按钮 */}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    登录中...
                  </>
                ) : (
                  <>
                    <LogIn className="h-4 w-4" />
                    登录
                  </>
                )}
              </Button>
            </form>

            {/* 演示账号说明 */}
            <div className="mt-6 rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
              <p className="font-medium mb-1">演示账号</p>
              <p>用户名：<code className="text-foreground">admin</code></p>
              <p>密码：<code className="text-foreground">admin123</code></p>
            </div>
          </CardContent>
        </Card>

        {/* 安全提示 */}
        <p className="mt-4 text-center text-xs text-white/40">
          安全连接 · 数据加密传输 · 仅限授权用户访问
        </p>
      </div>
    </div>
  )
}
