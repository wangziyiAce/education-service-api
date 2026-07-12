/**
 * 申请风险报告专用渲染器（重点报告 1/3）。
 *
 * 展示：风险评分矩阵、缺失材料清单、风险明细表格、行动建议。
 * 所有数字均来自后端，前端不计算风险分。
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import ReportSummaryPanel from '../ReportSummaryPanel'
import ReportExplanationPanel from '../ReportExplanationPanel'
import ReportMetadata from '../ReportMetadata'
import type { ReportDetailResponse, ApplicationRiskContent, ApplicationRiskItem, ReportActionSuggestion } from '@/types/report'
import { ShieldAlert, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

interface Props { report: ReportDetailResponse }

const RISK_LEVEL_CONFIG: Record<string, { label: string; variant: 'success' | 'warning' | 'destructive' | 'default'; icon: React.ComponentType<{ className?: string }> }> = {
  high: { label: '高风险', variant: 'destructive', icon: ShieldAlert },
  medium: { label: '中风险', variant: 'warning', icon: AlertTriangle },
  low: { label: '低风险', variant: 'success', icon: CheckCircle },
}

const PRIORITY_CONFIG: Record<string, string> = {
  urgent: '紧急', high: '高', medium: '中', low: '低',
}

export default function ApplicationRiskRenderer({ report }: Props) {
  const content = report.report_content as ApplicationRiskContent | null
  if (!content) {
    return <Card><CardContent className="py-8"><p className="text-center text-muted-foreground">报告内容为空</p></CardContent></Card>
  }

  const { metrics, risk_items, action_checklist, summary, explanation, metric_traces } = content

  return (
    <div className="space-y-6">
      {/* 风险指标卡片 */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        <MetricItem label="总申请数" value={metrics?.total_applications} />
        <MetricItem label="高风险" value={metrics?.high_risk_count} variant="destructive" />
        <MetricItem label="中风险" value={metrics?.medium_risk_count} variant="warning" />
        <MetricItem label="低风险" value={metrics?.low_risk_count} variant="success" />
        <MetricItem label="已逾期" value={metrics?.overdue_count} variant="destructive" />
        <MetricItem label="缺材料" value={metrics?.missing_material_count} variant="warning" />
      </div>

      {/* 风险明细表格 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">风险明细</CardTitle>
          <CardDescription>共 {risk_items?.length || 0} 条申请记录</CardDescription>
        </CardHeader>
        <CardContent>
          {(!risk_items || risk_items.length === 0) ? (
            <p className="text-sm text-muted-foreground text-center py-4">暂无风险记录</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">申请ID</TableHead>
                  <TableHead className="w-16">阶段</TableHead>
                  <TableHead className="w-16">风险分</TableHead>
                  <TableHead className="w-20">风险等级</TableHead>
                  <TableHead>风险原因</TableHead>
                  <TableHead>缺失材料</TableHead>
                  <TableHead>下一步</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {risk_items.slice(0, 50).map((item: ApplicationRiskItem) => {
                  const config = RISK_LEVEL_CONFIG[item.risk_level] || RISK_LEVEL_CONFIG.low
                  const Icon = config.icon
                  return (
                    <TableRow key={item.application_id}>
                      <TableCell className="text-xs">{item.application_id}</TableCell>
                      <TableCell className="text-xs">{item.stage || '-'}</TableCell>
                      <TableCell className="text-xs font-bold">{item.risk_score}</TableCell>
                      <TableCell>
                        <Badge variant={config.variant} className="text-[10px] gap-1">
                          <Icon className="h-3 w-3" />
                          {config.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {item.risk_reasons?.map((r: string) => (
                          <span key={r} className="mr-1 inline-block rounded bg-muted px-1 py-0.5">{r}</span>
                        ))}
                      </TableCell>
                      <TableCell className="text-xs max-w-32 truncate">
                        {item.missing_materials?.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="text-xs max-w-24 truncate">
                        {item.next_action || '暂无'}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 行动建议 */}
      {action_checklist && action_checklist.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">行动建议</CardTitle>
            <CardDescription>基于风险分析自动生成的建议行动项</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {action_checklist.map((action: ReportActionSuggestion, i: number) => (
                <div key={i} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
                    <span>{action.action}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {action.due_date && (
                      <span className="text-xs text-muted-foreground">截止: {action.due_date}</span>
                    )}
                    <Badge variant={action.priority === 'urgent' ? 'destructive' : action.priority === 'high' ? 'warning' : 'secondary'} className="text-[10px]">
                      {PRIORITY_CONFIG[action.priority] || action.priority}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI 分析 */}
      <ReportSummaryPanel summary={summary} />
      <ReportExplanationPanel explanation={explanation} />
      <ReportMetadata report={report} metricTraces={metric_traces} />
    </div>
  )
}

function MetricItem({ label, value, variant }: { label: string; value?: number; variant?: string }) {
  const colorClass = variant === 'destructive' ? 'text-destructive' : variant === 'warning' ? 'text-warning' : variant === 'success' ? 'text-success' : 'text-foreground'
  return (
    <div className="rounded-lg border bg-background p-3 text-center">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${colorClass}`}>{value ?? '-'}</p>
    </div>
  )
}
