/**
 * 智能报告 API。
 *
 * 对应后端 routers/report.py（8 个接口）:
 *   - GET    /reports/types
 *   - POST   /reports/generate
 *   - GET    /reports
 *   - GET    /reports/{id}
 *   - POST   /reports/{id}/retry
 *   - POST   /reports/{id}/actions
 *   - GET    /reports/{id}/actions
 *   - PATCH  /reports/actions/{action_id}
 */

import apiClient from '@/lib/api-client'
import type {
  ReportTypeDefinition,
  ReportGenerateRequest,
  ReportTaskResponse,
  ReportDetailResponse,
  ReportListResponse,
  ReportActionCreate,
  ReportActionResponse,
  ReportActionUpdate,
} from '@/types/report'

/** 获取全部 10 类报告类型定义 */
export function getReportTypes() {
  return apiClient.get<ReportTypeDefinition[]>('/reports/types')
}

/** 创建报告生成任务（返回 202 + task_id） */
export function generateReport(data: ReportGenerateRequest) {
  // 生成幂等键，防止重复提交
  const idempotencyKey = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  return apiClient.post<ReportTaskResponse>('/reports/generate', data, {
    headers: { 'Idempotency-Key': idempotencyKey },
  })
}

/** 分页查询报告列表 */
export function getReportList(params: {
  report_type?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) {
  return apiClient.get<ReportListResponse>('/reports', { params })
}

/** 查询报告详情（用于轮询） */
export function getReportDetail(id: number) {
  return apiClient.get<ReportDetailResponse>(`/reports/${id}`)
}

/** 失败报告重试 */
export function retryReport(id: number) {
  return apiClient.post<ReportTaskResponse>(`/reports/${id}/retry`)
}

/** 为该报告创建行动项 */
export function createReportAction(reportId: number, data: ReportActionCreate) {
  return apiClient.post<ReportActionResponse>(`/reports/${reportId}/actions`, data)
}

/** 查询报告的行动项列表 */
export function getReportActions(reportId: number) {
  return apiClient.get<ReportActionResponse[]>(`/reports/${reportId}/actions`)
}

/** 更新行动项 */
export function updateReportAction(actionId: number, data: ReportActionUpdate) {
  return apiClient.patch<ReportActionResponse>(`/reports/actions/${actionId}`, data)
}
