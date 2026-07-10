/**
 * 顶部操作栏组件。
 *
 * 职责：
 * 1. 显示面包屑或页面标题
 * 2. 用户下拉菜单（个人中心、退出登录）
 * 3. API 状态标记（开发模式可见）
 */

import { useAuthStore } from '@/stores/auth-store'
import { Button } from '@/components/ui/button'
import { LogOut, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function TopHeader() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const showTechStatus = import.meta.env.VITE_SHOW_TECH_STATUS === 'true'

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background px-6">
      {/* 左侧：留空或面包屑 */}
      <div className="flex items-center gap-2">
        {showTechStatus && (
          <span className="inline-flex items-center rounded bg-success/10 px-2 py-0.5 text-[10px] font-medium text-success">
            REAL
          </span>
        )}
      </div>

      {/* 右侧：用户菜单 */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-foreground font-medium">{user?.real_name || user?.username}</span>
          <span className="text-xs text-muted-foreground">
            ({user?.role_code === 'admin' ? '管理员' : user?.role_code === 'manager' ? '经理' : '员工'})
          </span>
        </div>
        <Button variant="ghost" size="icon" onClick={handleLogout} title="退出登录">
          <LogOut className="h-4 w-4" />
          <span className="sr-only">退出登录</span>
        </Button>
      </div>
    </header>
  )
}
