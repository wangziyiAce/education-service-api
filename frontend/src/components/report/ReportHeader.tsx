/**
 * 报告头部元信息组件。
 *
 * 展示报告的基本信息：类型、状态、周期、触发方式、生成时间等。
 */

import { Card, CardContent } from '@/components/ui/card'
import StatusBadge from '@/components/shared/StatusBadge'
import { format } from 'date-fns'
import type { ReportDetailResponse } from '@/types/report'
import { Calendar, Clock, User, Zap } from 'lucide-react'

interface ReportHeaderProps {
  report: ReportDetailResponse
}

const TRIGGER_LABELS: Record<string, string> = {
  manual: '手动生成',
  schedule: '定时生成',
  retry: '重试生成',
  system: '系统生成',
}

export default function ReportHeader({ report }: ReportHeaderProps) {
  return (
    <Card className="mb-4">
      <CardContent className="flex items-center gap-6 py-4 text-sm">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span>
            {report.period_start && report.period_end
              ? `${report.period_start} ~ ${report.period_end}`
              : '未指定周期'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Zap className="h-4 w-4" />
          <span>{TRIGGER_LABELS[report.trigger_source] || report.trigger_source}</span>
        </div>
        {report.generated_by && (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <User className="h-4 w-4" />
            <span>操作人 ID: {report.generated_by}</span>
          </div>
        )}
        {report.create_time && (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{format(new Date(report.create_time), 'yyyy-MM-dd HH:mm:ss')}</span>
          </div>
        )}
        <div className="flex-1" />
        <StatusBadge status={report.status} />
        {report.schema_version >= 2 && (
          <span className="text-xs text-muted-foreground">V{report.schema_version}</span>
        )}
      </CardContent>
    </Card>
  )
}
