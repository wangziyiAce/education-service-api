/**
 * 指标展示卡片。
 *
 * 职责：纯粹展示后端返回的数值，不执行任何计算。
 * 支持趋势指示（up/down/flat）和标题。
 *
 * 面试表达："前端 MetricCard 只负责格式化展示，不计算任何业务指标。
 * 所有数字（风险分、转化率、ROI）都来自后端 SQL 聚合和规则引擎。"
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'flat'
  trendLabel?: string
  /** 是否为 AI 生成内容（影响视觉样式） */
  aiGenerated?: boolean
  className?: string
}

const trendConfig = {
  up: { icon: TrendingUp, color: 'text-success' },
  down: { icon: TrendingDown, color: 'text-destructive' },
  flat: { icon: Minus, color: 'text-muted-foreground' },
}

export default function MetricCard({ title, value, unit, trend, trendLabel, aiGenerated, className }: MetricCardProps) {
  const TrendIcon = trend ? trendConfig[trend].icon : null
  const trendColor = trend ? trendConfig[trend].color : ''

  return (
    <Card className={cn(aiGenerated && 'border-dashed border-muted-foreground/30 bg-muted/20', className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
          {aiGenerated && (
            <span className="ml-2 inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
              AI 生成
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground">
          {value}
          {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
        </div>
        {trend && TrendIcon && (
          <p className={cn('mt-1 flex items-center gap-1 text-xs', trendColor)}>
            <TrendIcon className="h-3 w-3" />
            {trendLabel || trend}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
