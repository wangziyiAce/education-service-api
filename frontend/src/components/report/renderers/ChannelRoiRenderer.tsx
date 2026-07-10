/**
 * 渠道 ROI 报告专用渲染器（重点报告 2/3）。
 *
 * 展示：渠道投放指标、CPL/CAC/ROI 对比、数据质量警告。
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import ReportSummaryPanel from '../ReportSummaryPanel'
import ReportExplanationPanel from '../ReportExplanationPanel'
import ReportMetadata from '../ReportMetadata'
import type { ReportDetailResponse, ChannelROIContent } from '@/types/report'
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'

interface Props { report: ReportDetailResponse }

export default function ChannelRoiRenderer({ report }: Props) {
  const content = report.report_content as ChannelROIContent | null
  if (!content) {
    return <Card><CardContent className="py-8"><p className="text-center text-muted-foreground">报告内容为空</p></CardContent></Card>
  }

  const { channel_metrics, data_quality_warnings, summary, explanation, metric_traces } = content

  return (
    <div className="space-y-6">
      {/* 渠道指标表格 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-5 w-5 text-brand-600" />
            渠道投放指标
          </CardTitle>
          <CardDescription>Cost Per Lead / Customer Acquisition Cost / Return on Investment</CardDescription>
        </CardHeader>
        <CardContent>
          {(!channel_metrics || channel_metrics.length === 0) ? (
            <p className="text-sm text-muted-foreground text-center py-4">暂无渠道数据</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>渠道</TableHead>
                  <TableHead className="text-right">成本</TableHead>
                  <TableHead className="text-right">线索数</TableHead>
                  <TableHead className="text-right">CPL</TableHead>
                  <TableHead className="text-right">签约数</TableHead>
                  <TableHead className="text-right">CAC</TableHead>
                  <TableHead className="text-right">回款</TableHead>
                  <TableHead className="text-right">ROI</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(channel_metrics as Record<string, unknown>[]).map((ch: Record<string, unknown>, i: number) => {
                  const roi = ch.roi as number | null
                  return (
                    <TableRow key={i}>
                      <TableCell className="text-xs font-medium">{ch.channel as string || '-'}</TableCell>
                      <TableCell className="text-xs text-right">{formatNum(ch.cost)}</TableCell>
                      <TableCell className="text-xs text-right">{ch.leads as number || 0}</TableCell>
                      <TableCell className="text-xs text-right">{ch.cpl != null ? `¥${ch.cpl}` : '-'}</TableCell>
                      <TableCell className="text-xs text-right">{ch.signed_count as number || 0}</TableCell>
                      <TableCell className="text-xs text-right">{ch.cac != null ? `¥${ch.cac}` : '-'}</TableCell>
                      <TableCell className="text-xs text-right">{formatNum(ch.paid_amount)}</TableCell>
                      <TableCell className="text-xs text-right">
                        {roi != null ? (
                          <span className={`inline-flex items-center gap-1 ${roi >= 0 ? 'text-success' : 'text-destructive'}`}>
                            {roi >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                            {(roi * 100).toFixed(1)}%
                          </span>
                        ) : (
                          <Badge variant="secondary" className="text-[10px]">数据不足</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 数据质量警告 */}
      {data_quality_warnings && data_quality_warnings.length > 0 && (
        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside text-xs">
              {data_quality_warnings.map((w: string, i: number) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* AI 分析 */}
      <ReportSummaryPanel summary={summary} />
      <ReportExplanationPanel explanation={explanation} />
      <ReportMetadata report={report} metricTraces={metric_traces} />
    </div>
  )
}

function formatNum(value: unknown): string {
  if (value === null || value === undefined) return '-'
  const num = Number(value)
  if (isNaN(num)) return '-'
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return `¥${num.toLocaleString()}`
}
