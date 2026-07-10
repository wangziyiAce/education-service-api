/**
 * 业务状态标签组件。
 *
 * 将后端 ENUM 状态值映射为用户可见的中文文案和颜色。
 */

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STATUS_MAP: Record<string, { label: string; variant: 'success' | 'warning' | 'destructive' | 'secondary' | 'default' }> = {
  // 报告生成状态
  pending: { label: '等待生成', variant: 'warning' },
  generating: { label: '生成中', variant: 'warning' },
  completed: { label: '已完成', variant: 'success' },
  failed: { label: '生成失败', variant: 'destructive' },

  // 行动项状态
  confirmed: { label: '已确认', variant: 'success' },
  in_progress: { label: '执行中', variant: 'warning' },
  done: { label: '已完成', variant: 'success' },
  cancelled: { label: '已取消', variant: 'secondary' },

  // 启用状态
  enabled: { label: '已启用', variant: 'success' },
  disabled: { label: '已停用', variant: 'secondary' },
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_MAP[status] || { label: status, variant: 'default' as const }

  return (
    <Badge variant={config.variant} className={cn('text-xs', className)}>
      {config.label}
    </Badge>
  )
}
