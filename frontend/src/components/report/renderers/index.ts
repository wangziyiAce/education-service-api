/**
 * 报告渲染器注册表。
 *
 * 维护 report_type → V2 专用渲染组件的映射。
 * 未在此注册的报告类型自动使用 GenericV2Renderer。
 *
 * 三级策略：
 *   一级：注册表中的专用渲染器（当前 3 类）
 *   二级：schema_version < 2 → GenericV1Renderer
 *   三级：schema_version >= 2 但未注册 → GenericV2Renderer
 */

import type { ComponentType } from 'react'
import type { ReportDetailResponse } from '@/types/report'
import ApplicationRiskRenderer from './ApplicationRiskRenderer'
import ChannelRoiRenderer from './ChannelRoiRenderer'
import PsychWeeklyRenderer from './PsychWeeklyRenderer'

export interface ReportRendererProps {
  report: ReportDetailResponse
}

type RendererComponent = ComponentType<ReportRendererProps>

/** V2 专用渲染器注册表（按 report_type 映射） */
export const V2_RENDERERS: Record<string, RendererComponent> = {
  application_risk: ApplicationRiskRenderer,
  channel_roi: ChannelRoiRenderer,
  psych_weekly: PsychWeeklyRenderer,
}
