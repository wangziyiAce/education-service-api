import request from './request'

export const reportApi = {
  // 口述日报
  dictate: (data: { raw_content: string; report_date?: string }) =>
    request.post('/report/dictate', data),

  // 日报列表
  listReports: (params?: { employee_id?: number; start_date?: string; end_date?: string }) =>
    request.get('/report/', { params }),

  // 日报汇总
  getSummary: (reportDate: string) =>
    request.get('/report/summary', { params: { report_date: reportDate } }),
}

export const dailyReportApi = {
  // 员工日报
  listDailyReports: (params?: { employee_id?: number; start_date?: string; end_date?: string }) =>
    request.get('/employee/daily-reports', { params }),

  getSummary: (reportDate: string) =>
    request.get('/employee/daily-reports/summary', { params: { report_date: reportDate } }),

  getReport: (id: number) =>
    request.get(`/employee/daily-reports/${id}`),

  createReport: (data: { content: string; report_date?: string }) =>
    request.post('/employee/daily-reports', data),
}

// 报告助手
reportApi.assistantChat = (data: { message: string }) =>
  request.post('/report/assistant/messages', data)

// 报告数据
reportApi.listReportData = (params?: any) =>
  request.get('/report/data/application-materials', { params })
reportApi.createReportData = (data: any) =>
  request.post('/report/data/application-materials', data)

// 报告调度
reportApi.listSchedules = () =>
  request.get('/report/schedules')
reportApi.createSchedule = (data: any) =>
  request.post('/report/schedules', data)
reportApi.deleteSchedule = (id: number) =>
  request.delete(`/report/schedules/${id}`)

// 报告操作
reportApi.listActions = () =>
  request.get('/report/actions')
