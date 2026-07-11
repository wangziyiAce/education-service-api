/**
 * AI 摘要面板。
 *
 * 职责：展示 AI 生成的报告摘要，与核心业务数据区分开。
 * 使用灰色虚线边框 + "AI 生成" 标签，明确标识非确定性的 AI 内容。
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'

interface ReportSummaryPanelProps {
  summary?: string
}

export default function ReportSummaryPanel({ summary }: ReportSummaryPanelProps) {
  if (!summary || summary.trim() === '') return null

  return (
    <Card className="border-dashed border-muted-foreground/30 bg-muted/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          AI 分析摘要
          <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
            AI 生成
          </span>
        </CardTitle>
        <CardDescription>以下内容由 AI 基于业务数据自动生成，仅供参考</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
          {summary}
        </div>
      </CardContent>
    </Card>
  )
}
