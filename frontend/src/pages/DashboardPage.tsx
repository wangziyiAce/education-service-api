/**
 * 平台总览 Dashboard 页面。
 *
 * 首期展示真实内容（不造假 KPI）：
 * 1. 当前用户欢迎信息
 * 2. 智能报告中心入口卡片
 * 3. 最近生成的 5 条报告
 * 4. 智能助手入口（含状态标记）
 * 5. 后端服务状态
 */

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { FileText, FilePlus, CheckSquare, Users, MessageSquare, GraduationCap, Building2, TrendingUp, Clock } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getReportList } from '@/api/reports'
import StatusBadge from '@/components/shared/StatusBadge'
import LoadingState from '@/components/shared/LoadingState'
import ErrorState from '@/components/shared/ErrorState'
import EmptyState from '@/components/shared/EmptyState'
import { useAuthStore } from '@/stores/auth-store'
import { format } from 'date-fns'
import type { ReportTaskResponse } from '@/types/report'

/** 模块入口卡片配置 */
interface ModuleCard {
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  path: string
  status: 'available' | 'beta' | 'coming_soon'
  color: string
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  /** 查询最近 5 条报告 */
  const { data: reportList, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports', { page: 1, page_size: 5 }],
    queryFn: () => getReportList({ page: 1, page_size: 5 }),
    select: (res) => res.data,
  })

  /** 模块入口 */
  const reportModules: ModuleCard[] = [
    {
      title: '报告列表',
      description: '查看、筛选和管理所有生成的智能报告',
      icon: FileText,
      path: '/reports',
      status: 'available',
      color: 'text-brand-600 bg-brand-50',
    },
    {
      title: '生成报告',
      description: '选择报告类型，填写条件，一键生成智能分析报告',
      icon: FilePlus,
      path: '/reports/generate',
      status: 'available',
      color: 'text-success bg-success/10',
    },
    {
      title: '行动项',
      description: '跟踪报告建议的执行进度，形成管理闭环',
      icon: CheckSquare,
      path: '/reports/actions',
      status: 'beta',
      color: 'text-info bg-info/10',
    },
  ]

  const assistantModules: ModuleCard[] = [
    { title: '客户研判', description: '智能客户画像与产品匹配', icon: Users, path: '/customer-assessment', status: 'beta', color: 'text-warning bg-warning/10' },
    { title: '客服助手', description: 'RAG 知识库智能客服', icon: MessageSquare, path: '/customer-service', status: 'coming_soon', color: 'text-muted-foreground bg-muted' },
    { title: '学生助手', description: '学生个人学习与生活助手', icon: GraduationCap, path: '/student-assistant', status: 'coming_soon', color: 'text-muted-foreground bg-muted' },
    { title: '企业助手', description: '企业内部运营管理助手', icon: Building2, path: '/enterprise-assistant', status: 'coming_soon', color: 'text-muted-foreground bg-muted' },
  ]

  const statusBadge = (status: string) => {
    if (status === 'available') return null
    if (status === 'beta') return <Badge variant="warning" className="text-[10px]">Beta</Badge>
    return <Badge variant="secondary" className="text-[10px]">即将开放</Badge>
  }

  return (
    <div className="space-y-6">
      {/* 欢迎信息 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            欢迎回来，{user?.real_name || user?.username || '用户'}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            粤教智服 · 国际教育智能服务平台
          </p>
        </div>
        {import.meta.env.VITE_SHOW_TECH_STATUS === 'true' && (
          <Badge variant="success" className="text-xs">REAL</Badge>
        )}
      </div>

      {/* 智能报告中心 */}
      <section>
        <h2 className="mb-3 text-lg font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-brand-600" />
          智能报告中心
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {reportModules.map((mod) => {
            const Icon = mod.icon
            return (
              <Card
                key={mod.path}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => navigate(mod.path)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${mod.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    {statusBadge(mod.status)}
                  </div>
                  <CardTitle className="text-base mt-2">{mod.title}</CardTitle>
                  <CardDescription>{mod.description}</CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </section>

      {/* 智能助手入口 */}
      <section>
        <h2 className="mb-3 text-lg font-semibold flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-brand-600" />
          智能助手
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          {assistantModules.map((mod) => {
            const Icon = mod.icon
            return (
              <Card
                key={mod.path}
                className={`cursor-pointer transition-shadow hover:shadow-md ${mod.status === 'coming_soon' ? 'opacity-70' : ''}`}
                onClick={() => navigate(mod.path)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${mod.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    {statusBadge(mod.status)}
                  </div>
                  <p className="mt-2 text-sm font-medium">{mod.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{mod.description}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* 最近报告 */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Clock className="h-5 w-5 text-brand-600" />
            最近报告
          </h2>
          <Button variant="ghost" size="sm" onClick={() => navigate('/reports')}>
            查看全部
          </Button>
        </div>

        {isLoading && <LoadingState skeleton />}
        {isError && <ErrorState onRetry={() => refetch()} />}
        {!isLoading && !isError && reportList?.items?.length === 0 && (
          <Card>
            <CardContent className="py-8">
              <EmptyState
                title="还没有报告"
                description="前往「生成报告」创建第一份智能分析报告。"
                action={
                  <Button onClick={() => navigate('/reports/generate')}>
                    <FilePlus className="mr-2 h-4 w-4" />
                    生成报告
                  </Button>
                }
              />
            </CardContent>
          </Card>
        )}
        {!isLoading && !isError && reportList && reportList.items?.length > 0 && (
          <div className="space-y-2">
            {reportList.items.map((report: ReportTaskResponse) => (
              <Card
                key={report.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => navigate(`/reports/${report.id}`)}
              >
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{report.report_title}</p>
                    <p className="text-xs text-muted-foreground">
                      {report.report_type} · {report.create_time ? format(new Date(report.create_time), 'yyyy-MM-dd HH:mm') : '-'}
                    </p>
                  </div>
                  <StatusBadge status={report.status} />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
