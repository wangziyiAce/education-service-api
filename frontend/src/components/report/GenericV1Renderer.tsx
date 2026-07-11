/**
 * V1 兼容渲染器。
 *
 * 职责：当 schema_version < 2 时，以 JSON 查看器方式展示报告内容。
 * V1 报告没有定义的 Schema 结构，只能做通用展示。
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ReportDetailResponse } from '@/types/report'

interface GenericV1RendererProps {
  report: ReportDetailResponse
}

export default function GenericV1Renderer({ report }: GenericV1RendererProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">报告内容 (V1 兼容模式)</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="whitespace-pre-wrap break-words rounded-lg bg-muted p-4 text-xs leading-relaxed overflow-auto max-h-96">
          {JSON.stringify(report.report_content, null, 2)}
        </pre>
        {report.report_html && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-muted-foreground">查看后端渲染的 HTML</summary>
            <div
              className="mt-2 rounded-lg border p-4 text-sm"
              dangerouslySetInnerHTML={{ __html: report.report_html }}
            />
          </details>
        )}
      </CardContent>
    </Card>
  )
}
