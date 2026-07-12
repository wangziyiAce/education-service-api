/**
 * 报告行动项管理页面（P1）。
 *
 * 简化的行动项列表，支持查看状态和基本信息。
 */

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/components/shared/PageHeader'
import StatusBadge from '@/components/shared/StatusBadge'
import LoadingState from '@/components/shared/LoadingState'
import EmptyState from '@/components/shared/EmptyState'
import { getReportList } from '@/api/reports'
import { format } from 'date-fns'
import { CheckSquare } from 'lucide-react'

export default function ReportActionsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['reports', { page: 1, page_size: 100 }],
    queryFn: () => getReportList({ page: 1, page_size: 100 }),
    select: (res) => res.data,
  })

  return (
    <div>
      <PageHeader title="行动项管理" description="跟踪报告建议的执行进度" />

      {isLoading && <LoadingState skeleton />}
      {!isLoading && (!data || data.items.length === 0) && (
        <Card><CardContent className="py-8">
          <EmptyState
            title="暂无行动项"
            description="生成报告后，可将 AI 建议转为可跟踪的行动项"
            icon={<CheckSquare className="h-6 w-6 text-muted-foreground" />}
          />
        </CardContent></Card>
      )}
      {!isLoading && data && data.items.length > 0 && (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>报告ID</TableHead>
                <TableHead>报告标题</TableHead>
                <TableHead className="w-24">状态</TableHead>
                <TableHead className="w-40">创建时间</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="text-xs text-muted-foreground">{report.id}</TableCell>
                  <TableCell className="text-sm">{report.report_title}</TableCell>
                  <TableCell><StatusBadge status={report.status} /></TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {report.create_time ? format(new Date(report.create_time), 'yyyy-MM-dd') : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
