import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Lightbulb } from 'lucide-react'

interface ReportExplanationPanelProps {
  explanation?: string
}

export default function ReportExplanationPanel({ explanation }: ReportExplanationPanelProps) {
  if (!explanation || explanation.trim() === '') return null

  return (
    <Card className="border-dashed border-muted-foreground/30 bg-muted/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Lightbulb className="h-4 w-4 text-muted-foreground" />
          管理建议与解释
          <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
            AI 生成
          </span>
        </CardTitle>
        <CardDescription>以下管理建议由 AI 基于业务数据生成，执行前请结合实际情况判断</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
          {explanation}
        </div>
      </CardContent>
    </Card>
  )
}
