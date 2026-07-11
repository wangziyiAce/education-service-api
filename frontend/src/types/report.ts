/**
 * 智能报告相关 TypeScript 类型。
 *
 * 对齐后端：
 *   - schemas/report.py（API 请求/响应 Schema）
 *   - services/reporting/schemas.py（10 类报告内容模型）
 *   - services/reporting/registry.py（报告类型注册表）
 *
 * 所有字段结构已在阶段 0 契约审查中通过 Python 代码确认。
 */

import type { DataQuality, ReportStatus, TriggerSource, PaginatedResponse } from './common'

// ============================================================
//  报告类型元数据
// ============================================================

/** GET /api/v1/reports/types 返回的报告类型定义 */
export interface ReportTypeDefinition {
  report_type: string
  label: string
  schema_version: number
  allowed_roles: string[]
  template_name: string
  default_period_rule: string
  available_filters: string[]
  /** 该报告类型的内容 JSON Schema */
  json_schema: Record<string, unknown>
}

// ============================================================
//  报告生成
// ============================================================

/** POST /api/v1/reports/generate 请求体 */
export interface ReportGenerateRequest {
  report_type: string
  /** 兼容前端传 "title"，后端自动映射为 "report_title" */
  report_title: string
  period_start?: string | null
  period_end?: string | null
  filters?: Record<string, unknown>
}

/** 报告任务创建后的轻量响应（202 Accepted） */
export interface ReportTaskResponse {
  id: number
  report_type: string
  report_title: string
  status: ReportStatus
  schema_version: number
  period_start?: string | null
  period_end?: string | null
  trigger_source: TriggerSource
  generated_by?: number | null
  create_time?: string | null
}

/** 报告列表响应 */
export type ReportListResponse = PaginatedResponse<ReportTaskResponse>

/** GET /api/v1/reports/{id} 详情响应 */
export interface ReportDetailResponse extends ReportTaskResponse {
  report_content?: Record<string, unknown> | null
  report_html?: string | null
  data_quality?: DataQuality | null
  request_filters?: Record<string, unknown> | null
  aggregated_data_snapshot?: Record<string, unknown> | null
  error_code?: string | null
  error_message?: string | null
  started_time?: string | null
  completed_time?: string | null
  retry_of_report_id?: number | null
  retry_count: number
}

// ============================================================
//  报告行动项
// ============================================================

export interface ReportActionCreate {
  /** 兼容前端传 "suggestion"，后端自动映射为 "suggestion_text" */
  suggestion_text: string
  risk_code?: string | null
  owner_id?: number | null
  due_time?: string | null
  target_value?: number | null
}

export interface ReportActionResponse extends ReportActionCreate {
  id: number
  report_id: number
  status: string
  actual_value?: number | null
  completed_time?: string | null
  create_time?: string | null
  update_time?: string | null
}

export interface ReportActionUpdate {
  suggestion_text?: string | null
  risk_code?: string | null
  owner_id?: number | null
  due_time?: string | null
  status?: string | null
  target_value?: number | null
  actual_value?: number | null
  completed_time?: string | null
}

// ============================================================
//  报告定时计划
// ============================================================

export interface ReportScheduleCreate {
  report_type: string
  cron_expression: string
  enabled: number
  timezone: string
  period_rule: string
  title_template?: string | null
  filters: Record<string, unknown>
  recipients: Record<string, unknown>
}

export interface ReportScheduleResponse extends ReportScheduleCreate {
  id: number
  created_by?: number | null
  last_run_time?: string | null
  last_status?: string | null
  last_error?: string | null
  next_run_time?: string | null
  create_time?: string | null
  update_time?: string | null
}

// ============================================================
//  10 类报告内容模型（对齐 services/reporting/schemas.py）
// ============================================================

/** 所有报告内容共享的基础字段 */
export interface BaseReportContent {
  summary: string
  explanation: string
  metric_traces: MetricTrace[]
}

/** 指标追溯信息（对齐后端 MetricTrace） */
export interface MetricTrace {
  metric_name: string
  source_tables: string[]
  formula?: string | null
  filters: Record<string, unknown>
}

/** 申请风险指标 */
export interface ApplicationRiskMetrics {
  total_applications: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  overdue_count: number
  missing_material_count: number
}

/** 申请风险明细 */
export interface ApplicationRiskItem {
  application_id: number
  student_id?: number | null
  owner_id?: number | null
  stage: string
  risk_score: number
  risk_level: 'high' | 'medium' | 'low'
  risk_reasons: string[]
  missing_materials: string[]
  next_action?: string | null
}

/** 报告行动建议 */
export interface ReportActionSuggestion {
  owner_id?: number | null
  action: string
  due_date?: string | null
  priority: 'urgent' | 'high' | 'medium' | 'low'
}

export type CustomerOpsContent = BaseReportContent & {
  metrics: Record<string, unknown>
  stage_distribution: Record<string, unknown>[]
  stale_leads: Record<string, unknown>[]
  churn_analysis: Record<string, unknown>[]
}

export type DailySummaryContent = BaseReportContent & {
  metrics: Record<string, unknown>
  key_progress: string[]
  common_risks: string[]
  next_plans: string[]
}

export type WeeklySummaryContent = BaseReportContent & {
  business_sections: Record<string, unknown>
  cross_module_risks: string[]
  management_actions: string[]
}

export type PsychWeeklyContent = BaseReportContent & {
  metrics: Record<string, unknown>
  emotion_trend: Record<string, unknown>[]
  alert_status: Record<string, unknown>[]
  processing_timeliness: Record<string, unknown>
}

export type ComplaintWeeklyContent = BaseReportContent & {
  metrics: Record<string, unknown>
  sla_summary: Record<string, unknown>
  high_frequency_issues: Record<string, unknown>[]
}

export type ApplicationRiskContent = BaseReportContent & {
  metrics: ApplicationRiskMetrics
  risk_items: ApplicationRiskItem[]
  action_checklist: ReportActionSuggestion[]
}

export type SalesFunnelContent = BaseReportContent & {
  funnel_counts: Record<string, number>
  conversion_rates: Record<string, number | null>
  avg_stage_stay_days: Record<string, number | null>
  stalled_leads: Record<string, unknown>[]
  consultant_performance: Record<string, unknown>[]
}

export type ChannelROIContent = BaseReportContent & {
  channel_metrics: Record<string, unknown>[]
  data_quality_warnings: string[]
}

export type ServiceSLAContent = BaseReportContent & {
  sla_overview: Record<string, unknown>
  complaint_sla: Record<string, unknown>[]
  admin_service_sla: Record<string, unknown>[]
  psych_alert_sla: Record<string, unknown>[]
  backlog_aging: Record<string, unknown>[]
}

export type ActionClosureContent = BaseReportContent & {
  metrics: Record<string, unknown>
  overdue_actions: Record<string, unknown>[]
  repeated_issues: Record<string, unknown>[]
  target_achievement: Record<string, unknown>[]
}

/** 报告内容联合类型 */
export type ReportContentUnion =
  | CustomerOpsContent
  | DailySummaryContent
  | WeeklySummaryContent
  | PsychWeeklyContent
  | ComplaintWeeklyContent
  | ApplicationRiskContent
  | SalesFunnelContent
  | ChannelROIContent
  | ServiceSLAContent
  | ActionClosureContent
  | Record<string, unknown> // V1 兼容

// ============================================================
//  报告类型展示配置（本地保留，不可作为数据源）
// ============================================================

/** 报告类型的展示配置（图标、重点色） */
export interface ReportPresentation {
  icon: string
  accent: 'default' | 'warning' | 'info' | 'success' | 'danger'
  description: string
}

/** 10 类报告的展示配置 */
export const REPORT_PRESENTATION: Record<string, ReportPresentation> = {
  customer_ops: { icon: 'Users', accent: 'info', description: '客户阶段分布、停滞线索、流失风险分析' },
  daily_summary: { icon: 'ClipboardList', accent: 'default', description: '员工日报汇总、关键进展、共性问题' },
  weekly_summary: { icon: 'BarChart3', accent: 'info', description: '跨模块综合经营周报、管理行动建议' },
  psych_weekly: { icon: 'Heart', accent: 'danger', description: '心理预警分布、情绪趋势、首次跟进时效' },
  complaint_weekly: { icon: 'MessageSquareWarning', accent: 'warning', description: '投诉分类统计、SLA 时效、高频问题' },
  application_risk: { icon: 'ShieldAlert', accent: 'warning', description: '申请材料风险评分、缺失追踪、行动建议' },
  sales_funnel: { icon: 'Funnel', accent: 'info', description: '销售漏斗转化率、阶段停留、停滞线索' },
  channel_roi: { icon: 'DollarSign', accent: 'success', description: '渠道投放成本、CPL/CAC/ROI 对比' },
  service_sla: { icon: 'Clock', accent: 'warning', description: '服务响应/解决时效、积压老化分析' },
  action_closure: { icon: 'CheckCircle', accent: 'success', description: '行动完成率、逾期追踪、重复问题' },
}
