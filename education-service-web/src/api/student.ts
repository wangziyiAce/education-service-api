import request from './request'
import type { LeaveRecord, LeaveCreate, LeaveApprove, FeedbackTicket, FeedbackCreate, FeedbackUpdate, PsychAlert, PsychAlertUpdate, Score, ApplicationProgress, AcademicDeadline, StudentNotification } from '@/types/student'
import type { PaginatedData } from '@/types/api'

export const studentApi = {
  // 请假
  listLeaves: (params: { student_id: number; status?: string; page?: number; page_size?: number }): Promise<PaginatedData<LeaveRecord>> =>
    request.get('/student/leave-requests', { params }),

  listAllLeaves: (params?: { status?: string; page?: number; page_size?: number }): Promise<PaginatedData<LeaveRecord>> =>
    request.get('/student/leave-requests', { params }),

  createLeave: (data: LeaveCreate): Promise<LeaveRecord> =>
    request.post('/student/leave-requests', data),

  approveLeave: (requestId: number, data: LeaveApprove): Promise<any> =>
    request.put(`/student/leave-requests/${requestId}/approve`, data),

  cancelLeave: (requestId: number, studentId: number): Promise<any> =>
    request.put(`/student/leave-requests/${requestId}/cancel`, null, { params: { student_id: studentId } }),

  // 投诉
  listFeedbacks: (params: { student_id: number; status?: string; page?: number; page_size?: number }): Promise<PaginatedData<FeedbackTicket>> =>
    request.get('/student/feedback-tickets', { params }),

  listAllFeedbacks: (params?: { status?: string; page?: number; page_size?: number }): Promise<PaginatedData<FeedbackTicket>> =>
    request.get('/student/feedback-tickets', { params }),

  createFeedback: (data: FeedbackCreate): Promise<FeedbackTicket> =>
    request.post('/student/feedback-tickets', data),

  updateFeedback: (ticketId: number, data: FeedbackUpdate): Promise<any> =>
    request.put(`/student/feedback-tickets/${ticketId}`, data),

  // 心理预警
  listPsychAlerts: (params?: { risk_level?: string; status?: string; page?: number; page_size?: number }): Promise<PaginatedData<PsychAlert>> =>
    request.get('/student/psych/alerts', { params }),

  handlePsychAlert: (alertId: number, data: PsychAlertUpdate): Promise<any> =>
    request.put(`/student/psych/alerts/${alertId}`, data),

  // 成绩
  listScores: (params: { student_id: number; semester?: string; page?: number; page_size?: number }): Promise<PaginatedData<Score>> =>
    request.get('/student/scores', { params }),

  // 申请进度
  listApplications: (params: { student_id: number; page?: number; page_size?: number }): Promise<PaginatedData<ApplicationProgress>> =>
    request.get('/student/applications', { params }),

  // 学业DDL
  listDeadlines: (params: { student_id: number; upcoming_days?: number; page?: number; page_size?: number }): Promise<PaginatedData<AcademicDeadline>> =>
    request.get('/student/deadlines', { params }),

  // 通知
  listNotifications: (params: { student_id: number; only_unread?: boolean; page?: number; page_size?: number }): Promise<PaginatedData<StudentNotification>> =>
    request.get('/student/notifications', { params }),

  markRead: (notificationId: number, studentId: number): Promise<any> =>
    request.put(`/student/notifications/${notificationId}/read`, null, { params: { student_id: studentId } }),

  markAllRead: (studentId: number): Promise<any> =>
    request.put('/student/notifications/read-all', null, { params: { student_id: studentId } }),
}
