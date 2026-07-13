import request from './request'
import type { Course, Event, EventRegistrationCreate, EventRegistration, ChatSession, ChatMessage } from '@/types/chat'
import type { PaginatedData } from '@/types/api'

export const chatApi = {
  // 课程
  listCourses: (params?: Record<string, any>): Promise<PaginatedData<Course>> =>
    request.get('/courses', { params }),

  getCourse: (id: number): Promise<Course> =>
    request.get(`/courses/${id}`),

  // 活动
  listEvents: (params?: Record<string, any>): Promise<PaginatedData<Event>> =>
    request.get('/events', { params }),

  getEvent: (id: number): Promise<Event> =>
    request.get(`/events/${id}`),

  // 活动报名
  registerEvent: (eventId: number, data: EventRegistrationCreate): Promise<EventRegistration> =>
    request.post(`/events/${eventId}/register`, data),

  cancelRegistration: (eventId: number, userId: number): Promise<any> =>
    request.delete(`/events/${eventId}/register`, { params: { user_id: userId } }),

  // 会话
  createSession: (data: { user_id?: number; visitor_name?: string; visitor_contact?: string }): Promise<ChatSession> =>
    request.post('/chat/session', data),

  // 消息
  saveMessage: (sessionId: string, data: { role: string; content: string; intent?: string }): Promise<ChatMessage> =>
    request.post(`/chat/session/${sessionId}/messages`, data),

  listMessages: (sessionId: string, params?: { cursor?: number; limit?: number }): Promise<any> =>
    request.get(`/chat/session/${sessionId}/messages`, { params }),
}
