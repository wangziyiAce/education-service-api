/**
 * 通用 V2 报告渲染器。
 *
 * 职责：当某类报告没有专用渲染器时，使用此通用组件。
 * 它能渲染：指标卡片、表格、列表、Summary、Explanation——保证所有 10 类报告至少可正常展示。
 *
 * 事实与 AI 分区原则：
 *   - 业务数字（metrics, items, checklist）→ 白色卡片，彩色标题
 *   - AI 内容（summary, explanation）→ 灰色背景，带 "AI 生成" 标签
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import ReportSummaryPanel from './ReportSummaryPanel'
import ReportExplanationPanel from './ReportExplanationPanel'
import ReportMetadata from './ReportMetadata'
import type { ReportDetailResponse } from '@/types/report'

interface GenericV2RendererProps {
  report: ReportDetailResponse
}

export default function GenericV2Renderer({ report }: GenericV2RendererProps) {
  const content = report.report_content as Record<string, unknown> | null
  if (!content) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">报告内容为空</p>
        </CardContent>
      </Card>
    )
  }

  const { summary, explanation, metric_traces, ...rest } = content

  return (
    <div className="space-y-6">
      {/* ---- 核心业务数据区 ---- */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <span className="inline-block h-3 w-3 rounded-sm bg-brand-600" />
            核心业务数据
          </CardTitle>
          <CardDescription>以下数据来自数据库聚合和规则引擎，非 AI 生成</CardDescription>
        </CardHeader>
        <CardContent>
          {/* 指标卡片 */}
          {renderMetrics(rest)}
          {/* 列表/数组数据 */}
          {renderLists(rest)}
          {/* 其他字段以 JSON 展示 */}
          {renderRemainingFields(rest)}
        </CardContent>
      </Card>

      {/* ---- AI 分析区 ---- */}
      <ReportSummaryPanel summary={summary as string} />
      <ReportExplanationPanel explanation={explanation as string} />

      {/* ---- 报告元信息 ---- */}
      <ReportMetadata report={report} metricTraces={metric_traces} />
    </div>
  )
}

/** 渲染指标数字为卡片 */
function renderMetrics(data: Record<string, unknown>) {
  const numericFields: [string, unknown][] = []
  const sharedKeys = ['summary', 'explanation', 'metric_traces']

  for (const [key, value] of Object.entries(data)) {
    if (sharedKeys.includes(key)) continue
    if (typeof value === 'number' || (typeof value === 'string' && !isNaN(Number(value)) && String(value).length < 10)) {
      numericFields.push([key, value])
    }
  }

  if (numericFields.length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 mb-6">
      {numericFields.map(([key, value]) => (
        <div key={key} className="rounded-lg border bg-background p-3">
          <p className="text-xs text-muted-foreground capitalize">{formatKey(key)}</p>
          <p className="mt-1 text-xl font-bold text-foreground">{String(value)}</p>
        </div>
      ))}
    </div>
  )
}

/** 渲染数组数据为表格 */
function renderLists(data: Record<string, unknown>) {
  const sharedKeys = ['summary', 'explanation', 'metric_traces']
  const arrayFields = Object.entries(data).filter(
    ([key, value]) => !sharedKeys.includes(key) && Array.isArray(value) && value.length > 0
  )

  if (arrayFields.length === 0) return null

  return (
    <div className="space-y-4">
      {arrayFields.map(([key, items]) => {
        const arr = items as Record<string, unknown>[]
        if (arr.length === 0) return null

        // 提取该数组中出现过的所有键
        const keys = [...new Set(arr.flatMap((item) => Object.keys(item)))].slice(0, 8)

        return (
          <div key={key}>
            <h4 className="mb-2 text-sm font-medium text-foreground">{formatKey(key)} ({arr.length})</h4>
            <div className="rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    {keys.map((k) => (
                      <TableHead key={k} className="text-xs">{formatKey(k)}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {arr.slice(0, 20).map((item, i) => (
                    <TableRow key={i}>
                      {keys.map((k) => (
                        <TableCell key={k} className="text-xs">{renderCellValue(item[k])}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {arr.length > 20 && (
              <p className="mt-1 text-xs text-muted-foreground">
                仅显示前 20 条，共 {arr.length} 条
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}

/** 渲染剩余非数值、非数组的字段 */
function renderRemainingFields(data: Record<string, unknown>) {
  const sharedKeys = ['summary', 'explanation', 'metric_traces']
  const rendered = new Set<string>()
  const remaining = Object.entries(data).filter(([key, value]) => {
    if (sharedKeys.includes(key)) return false
    if (typeof value === 'number') { rendered.add(key); return false }
    if (Array.isArray(value)) { rendered.add(key); return false }
    return true
  })

  if (remaining.length === 0) return null

  return (
    <details className="mt-4">
      <summary className="cursor-pointer text-xs text-muted-foreground">查看其他字段</summary>
      <pre className="mt-2 whitespace-pre-wrap break-words rounded-lg bg-muted p-3 text-xs overflow-auto max-h-48">
        {JSON.stringify(Object.fromEntries(remaining), null, 2)}
      </pre>
    </details>
  )
}

function formatKey(key: string): string {
  const labelMap: Record<string, string> = {
    risk_items: '风险明细',
    action_checklist: '行动建议',
    missing_materials: '缺失材料',
    risk_reasons: '风险原因',
    risk_score: '风险分',
    risk_level: '风险等级',
    stage_distribution: '阶段分布',
    stale_leads: '停滞线索',
    churn_analysis: '流失分析',
    key_progress: '关键进展',
    common_risks: '共性问题',
    next_plans: '下一步计划',
    funnel_counts: '漏斗数量',
    conversion_rates: '转化率',
    stalled_leads: '停滞线索',
    consultant_performance: '顾问业绩',
    channel_metrics: '渠道指标',
    sla_overview: 'SLA 概览',
    complaint_sla: '投诉 SLA',
    backlog_aging: '积压老化',
    overdue_actions: '逾期行动项',
    repeated_issues: '重复问题',
    target_achievement: '目标达成',
  }
  return labelMap[key] || key.replace(/_/g, ' ')
}

function renderCellValue(value: unknown): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 100)
  return String(value)
}
