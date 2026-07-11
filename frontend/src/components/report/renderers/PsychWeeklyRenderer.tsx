/**
 * 心理预警周报专用渲染器（重点报告 3/3）。
 *
 * 隐私边界：
 *   - 展示：风险等级分布、预警状态、首次跟进时效、匿名趋势、匿名统计
 *   - 禁止：咨询原文、诊断性描述、学生身份信息、可识别个人的长文本
 *
 * 此组件通过数据筛选保证隐私安全（后端已过滤敏感字段）。
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import ReportSummaryPanel from '../ReportSummaryPanel'
import ReportExplanationPanel from '../ReportExplanationPanel'
import ReportMetadata from '../ReportMetadata'
import type { ReportDetailResponse, PsychWeeklyContent } from '@/types/report'
import { Heart, Shield, AlertTriangle } from 'lucide-react'

interface Props { report: ReportDetailResponse }

export default function PsychWeeklyRenderer({ report }: Props) {
  const content = report.report_content as PsychWeeklyContent | null
  if (!content) {
    return <Card><CardContent className="py-8"><p className="text-center text-muted-foreground">报告内容为空</p></CardContent></Card>
  }

  const { metrics, alert_status, processing_timeliness, summary, explanation, metric_traces } = content

  return (
    <div className="space-y-6">
      {/* 隐私保护声明 */}
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription className="text-xs">
          本报告仅展示匿名统计数据和趋势分析。所有咨询原文、学生身份信息和诊断性描述均已按隐私保护策略过滤。
        </AlertDescription>
      </Alert>

      {/* 风险等级分布 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Heart className="h-5 w-5 text-destructive" />
            风险等级分布
          </CardTitle>
          <CardDescription>本周期内的预警等级统计</CardDescription>
        </CardHeader>
        <CardContent>
          {metrics ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(metrics as Record<string, unknown>).map(([key, value]) => (
                <div key={key} className="rounded-lg border bg-background p-3 text-center">
                  <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="mt-1 text-xl font-bold text-foreground">{String(value ?? '-')}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">暂无统计数据</p>
          )}
        </CardContent>
      </Card>

      {/* 预警状态列表 */}
      {alert_status && Array.isArray(alert_status) && alert_status.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-warning" />
              预警状态
            </CardTitle>
            <CardDescription>共 {alert_status.length} 条预警记录（已匿名处理）</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>风险等级</TableHead>
                  <TableHead>处理状态</TableHead>
                  <TableHead>首次响应</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(alert_status as Record<string, unknown>[]).slice(0, 30).map((item, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-xs text-muted-foreground">{i + 1}</TableCell>
                    <TableCell>
                      <Badge variant={item.risk_level === 'high' ? 'destructive' : item.risk_level === 'medium' ? 'warning' : 'secondary'} className="text-[10px]">
                        {String(item.risk_level || '-')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">{String(item.status || '-')}</TableCell>
                    <TableCell className="text-xs">{String(item.first_response_hours || '-')}小时</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {alert_status.length > 30 && (
              <p className="mt-2 text-xs text-muted-foreground">仅显示前 30 条，共 {alert_status.length} 条</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 处理时效 */}
      {processing_timeliness && Object.keys(processing_timeliness as Record<string, unknown>).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">首次跟进时效</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(processing_timeliness as Record<string, unknown>).map(([key, value]) => (
                <div key={key} className="rounded-lg border bg-background p-3">
                  <p className="text-xs text-muted-foreground">{key}</p>
                  <p className="mt-1 text-lg font-bold">{String(value ?? '-')}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI 分析（仅匿名统计摘要） */}
      <ReportSummaryPanel summary={summary} />
      <ReportExplanationPanel explanation={explanation} />
      <ReportMetadata report={report} metricTraces={metric_traces} />
    </div>
  )
}
