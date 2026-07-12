/**
 * 报告定时计划页面（P1）。
 *
 * 简化的定时计划列表页面。
 */

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import PageHeader from '@/components/shared/PageHeader'
import LoadingState from '@/components/shared/LoadingState'
import EmptyState from '@/components/shared/EmptyState'
import { getScheduleList } from '@/api/report-schedules'
import { CalendarClock } from 'lucide-react'

export default function ReportSchedulesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => getScheduleList(),
    select: (res) => res.data,
  })

  return (
    <div>
      <PageHeader title="报告计划" description="管理定时报告生成任务" />

      {isLoading && <LoadingState skeleton />}
      {!isLoading && (!data || data.length === 0) && (
        <Card><CardContent className="py-8">
          <EmptyState
            title="暂无定时计划"
            description="尚未配置定时报告生成计划"
            icon={<CalendarClock className="h-6 w-6 text-muted-foreground" />}
          />
        </CardContent></Card>
      )}
      {!isLoading && data && data.length > 0 && (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">ID</TableHead>
                <TableHead>报告类型</TableHead>
                <TableHead>Cron 表达式</TableHead>
                <TableHead className="w-20">状态</TableHead>
                <TableHead className="w-40">最近运行</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell className="text-xs text-muted-foreground">{schedule.id}</TableCell>
                  <TableCell className="text-sm">{schedule.report_type}</TableCell>
                  <TableCell className="text-xs font-mono">{schedule.cron_expression}</TableCell>
                  <TableCell>
                    <Badge variant={schedule.enabled ? 'success' : 'secondary'} className="text-[10px]">
                      {schedule.enabled ? '启用' : '停用'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{schedule.last_run_time || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
