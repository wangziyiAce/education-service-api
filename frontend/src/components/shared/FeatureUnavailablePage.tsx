/**
 * 功能暂未开放统一页面。
 *
 * 用于所有尚未开发完成的模块（客服助手、学生助手、企业助手等）。
 * 导航保留入口、可点击，进入此页面展示功能规划和当前状态。
 * 不调用虚假 API，不显示假数据。
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Clock,
  FlaskConical,
  ArrowLeft,
  Sparkles,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface FeatureUnavailablePageProps {
  feature: string
  status: 'beta' | 'coming_soon' | 'testing'
  description: string
  plannedCapabilities: string[]
  integrationNote: string
}

const statusConfig = {
  beta: { label: 'Beta', variant: 'warning' as const, icon: FlaskConical },
  coming_soon: { label: '即将开放', variant: 'secondary' as const, icon: Clock },
  testing: { label: '联调中', variant: 'default' as const, icon: Sparkles },
}

export default function FeatureUnavailablePage({
  feature,
  status,
  description,
  plannedCapabilities,
  integrationNote,
}: FeatureUnavailablePageProps) {
  const navigate = useNavigate()
  const config = statusConfig[status]
  const StatusIcon = config.icon

  return (
    <div className="mx-auto max-w-2xl py-12">
      {/* 功能标识 */}
      <div className="text-center mb-8">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <StatusIcon className="h-8 w-8 text-muted-foreground" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-foreground">{feature}</h1>
        <div className="mt-2">
          <Badge variant={config.variant} className="text-sm px-3 py-1">
            {config.label}
          </Badge>
        </div>
        <p className="mt-3 text-muted-foreground max-w-md mx-auto">{description}</p>
      </div>

      {/* 规划能力 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">规划能力</CardTitle>
          <CardDescription>该模块预计支持以下功能</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {plannedCapabilities.map((cap, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 block h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                <span className="text-muted-foreground">{cap}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* 集成状态 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">当前状态</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{integrationNote}</p>
        </CardContent>
      </Card>

      {/* 返回按钮 */}
      <div className="mt-8 text-center">
        <Button variant="outline" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回工作台
        </Button>
      </div>
    </div>
  )
}
