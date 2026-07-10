/**
 * 报告渲染器调度入口。
 *
 * 职责：根据 report_type + schema_version 从注册表选择对应的渲染组件。
 *
 * 三级策略：
 *   一级：专用渲染器（3 类重点报告）→ application_risk, channel_roi, psych_weekly
 *   二级：schema_version=1 → JSON 查看器
 *   三级：schema_version=2 但无专用渲染器 → GenericV2Renderer（通用渲染）
 */

import type { ReportDetailResponse } from '@/types/report'
import GenericV2Renderer from './GenericV2Renderer'
import GenericV1Renderer from './GenericV1Renderer'
import { V2_RENDERERS } from './renderers/index'

interface ReportRendererProps {
  report: ReportDetailResponse
}

export default function ReportRenderer({ report }: ReportRendererProps) {
  // schema_version < 2：使用 V1 兼容渲染器（JSON 查看器）
  if (report.schema_version < 2) {
    return <GenericV1Renderer report={report} />
  }

  // schema_version >= 2：查找专用渲染器
  const Renderer = V2_RENDERERS[report.report_type]
  if (Renderer) {
    return <Renderer report={report} />
  }

  // 回退到通用 V2 渲染器
  return <GenericV2Renderer report={report} />
}
