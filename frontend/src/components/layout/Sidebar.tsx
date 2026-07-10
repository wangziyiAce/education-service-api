/**
 * 左侧导航栏组件。
 *
 * 职责：
 * 1. 显示产品 Logo 和名称"粤教智服"
 * 2. 展示导航菜单（工作台、智能报告、智能助手、系统管理）
 * 3. 高亮当前路由（NavLink active 样式）
 * 4. 支持折叠/展开（响应式）
 *
 * 导航结构对齐首期计划：P0 真实 → P1 标记 → P2 即将开放 → P3 隐藏
 */

import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FileText,
  FilePlus,
  CheckSquare,
  Users,
  MessageSquare,
  GraduationCap,
  Building2,
  CalendarClock,
  Database,
  ChevronDown,
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { ROLE_CODES } from '@/types/auth'

interface NavItem {
  label: string
  icon: React.ComponentType<{ className?: string }>
  to?: string
  badge?: string
  badgeVariant?: 'default' | 'warning' | 'info'
  children?: NavItem[]
}

export default function Sidebar() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role_code === ROLE_CODES.ADMIN || user?.role_code === ROLE_CODES.MANAGER

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['reports', 'assistants']))

  const toggleGroup = (key: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const navGroups: { key: string; label: string; items: NavItem[] }[] = [
    {
      key: 'main',
      label: '',
      items: [
        { label: '工作台', icon: LayoutDashboard, to: '/dashboard' },
      ],
    },
    {
      key: 'reports',
      label: '智能报告',
      items: [
        { label: '报告列表', icon: FileText, to: '/reports' },
        { label: '生成报告', icon: FilePlus, to: '/reports/generate' },
        { label: '行动项', icon: CheckSquare, to: '/reports/actions', badge: 'P1', badgeVariant: 'info' },
      ],
    },
    {
      key: 'assistants',
      label: '智能助手',
      items: [
        { label: '客户研判', icon: Users, to: '/customer-assessment', badge: 'Beta', badgeVariant: 'warning' },
        { label: '客服助手', icon: MessageSquare, to: '/customer-service', badge: '即将开放', badgeVariant: 'default' },
        { label: '学生助手', icon: GraduationCap, to: '/student-assistant', badge: '即将开放', badgeVariant: 'default' },
        { label: '企业助手', icon: Building2, to: '/enterprise-assistant', badge: '即将开放', badgeVariant: 'default' },
      ],
    },
  ]

  // 管理员可见系统管理
  if (isAdmin) {
    navGroups.push({
      key: 'admin',
      label: '系统管理',
      items: [
        { label: '报告计划', icon: CalendarClock, to: '/reports/schedules' },
        { label: '数据维护', icon: Database, to: '/reports/schedules', badge: '暂不可用', badgeVariant: 'default' },
      ],
    })
  }

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-56 flex-col bg-sidebar-background text-sidebar-foreground">
      {/* Logo + 品牌名 */}
      <div className="flex h-14 items-center gap-3 border-b border-sidebar-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground font-bold text-sm">
          粤
        </div>
        <span className="text-sm font-semibold text-white">粤教智服</span>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 overflow-y-auto py-4 space-y-4">
        {navGroups.map((group) => (
          <div key={group.key} className="px-3">
            {group.label && (
              <button
                onClick={() => toggleGroup(group.key)}
                className="flex w-full items-center justify-between px-3 py-1 text-xs font-medium text-sidebar-foreground/60 uppercase tracking-wider"
              >
                {group.label}
                <ChevronDown
                  className={cn(
                    'h-3 w-3 transition-transform',
                    expandedGroups.has(group.key) && 'rotate-180'
                  )}
                />
              </button>
            )}
            {(!group.label || expandedGroups.has(group.key)) && (
              <ul className="mt-1 space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon
                  return (
                    <li key={item.to || item.label}>
                      <NavLink
                        to={item.to || '#'}
                        className={({ isActive: linkActive }) =>
                          cn(
                            'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                            linkActive
                              ? 'bg-sidebar-primary text-sidebar-primary-foreground font-medium'
                              : 'text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                          )
                        }
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        <span className="flex-1 truncate">{item.label}</span>
                        {item.badge && (
                          <span
                            className={cn(
                              'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium shrink-0',
                              item.badgeVariant === 'warning' && 'bg-warning/20 text-warning',
                              item.badgeVariant === 'info' && 'bg-info/20 text-info',
                              item.badgeVariant === 'default' && 'bg-sidebar-accent text-sidebar-foreground/60'
                            )}
                          >
                            {item.badge}
                          </span>
                        )}
                      </NavLink>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        ))}
      </nav>

      {/* 底部用户信息 */}
      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sidebar-primary text-white text-xs font-medium">
            {user?.real_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.real_name || user?.username || '未登录'}
            </p>
            <p className="text-xs text-sidebar-foreground/50 truncate">
              {user?.role_code === 'admin' ? '管理员' :
               user?.role_code === 'manager' ? '经理' :
               user?.role_code === 'team_leader' ? '团队主管' :
               user?.role_code === 'employee' ? '员工' :
               user?.role_code === 'student' ? '学生' : '未知'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}
