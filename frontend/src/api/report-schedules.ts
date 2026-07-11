/**
 * 报告定时计划 API。
 *
 * 对应后端 routers/report_schedule.py:
 *   CRUD /api/v1/report-schedules
 */

import apiClient from '@/lib/api-client'
import type { ReportScheduleCreate, ReportScheduleResponse } from '@/types/report'

export function createSchedule(data: ReportScheduleCreate) {
  return apiClient.post<ReportScheduleResponse>('/report-schedules', data)
}

export function getScheduleList(params?: { enabled?: number }) {
  return apiClient.get<ReportScheduleResponse[]>('/report-schedules', { params })
}

export function getSchedule(id: number) {
  return apiClient.get<ReportScheduleResponse>(`/report-schedules/${id}`)
}

export function updateSchedule(id: number, data: Partial<ReportScheduleCreate>) {
  return apiClient.patch<ReportScheduleResponse>(`/report-schedules/${id}`, data)
}

export function deleteSchedule(id: number) {
  return apiClient.delete(`/report-schedules/${id}`)
}
