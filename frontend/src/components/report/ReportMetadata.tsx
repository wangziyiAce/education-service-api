/**
 * 报告元信息组件。
 *
 * 展示报告的生成元信息：生成时间、耗时、Schema 版本、重试链、指标追溯。
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { format } from 'date-fns'
import type { ReportDetailResponse, MetricTrace } from '@/types/report'
import { Clock, Database, GitBranch, Hash } from 'lucide-react'

interface ReportMetadataProps {
  report: ReportDetailResponse
  metricTraces?: unknown
}

export default function ReportMetadata({ report, metricTraces }: ReportMetadataProps) {
  const traces = metricTraces as MetricTrace[] | undefined

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">报告元信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">开始时间：</span>
            <span>{report.started_time ? format(new Date(report.started_time), 'HH:mm:ss') : '-'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">完成时间：</span>
            <span>{report.completed_time ? format(new Date(report.completed_time), 'HH:mm:ss') : '-'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Hash className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Schema 版本：</span>
            <span>V{report.schema_version}</span>
          </div>
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">数据来源：</span>
            <span>{report.data_quality?.data_source || 'unknown'}</span>
          </div>
        </div>

        {/* 重试链 */}
        {report.retry_count > 0 && (
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">重试次数：{report.retry_count}</span>
            {report.retry_of_report_id && (
              <span className="text-muted-foreground">(原报告 ID: {report.retry_of_report_id})</span>
            )}
          </div>
        )}

        {/* 指标追溯 */}
        {traces && traces.length > 0 && (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-muted-foreground">
              指标追溯（{traces.length} 项指标）
            </summary>
            <div className="mt-2 space-y-1">
              {traces.map((trace, i) => (
                <div key={i} className="rounded bg-muted px-2 py-1 text-xs">
                  <span className="font-medium">{trace.metric_name}</span>
                  {trace.source_tables && trace.source_tables.length > 0 && (
                    <span className="text-muted-foreground"> ← {trace.source_tables.join(', ')}</span>
                  )}
                  {trace.formula && (
                    <span className="text-muted-foreground"> · 公式: {trace.formula}</span>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}
      </CardContent>
    </Card>
  )
}
