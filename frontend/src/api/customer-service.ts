import apiClient from '@/lib/api-client'
type Envelope<T> = { code: number; message: string; data: T }
export interface Course { id: number; project_name: string; category?: string; description?: string; duration?: string; price?: number }
export interface EventItem { id: number; event_name: string; start_time: string; location?: string; status: string }
export interface Message { id: number; role: string; content: string; create_time: string }
const unwrap = <T>(r: { data: Envelope<T> }) => r.data.data
export const getCourses = () => apiClient.get<Envelope<{ items: Course[] }>>('/client/courses').then(unwrap)
export const getEvents = () => apiClient.get<Envelope<{ items: EventItem[] }>>('/client/events').then(unwrap)
export const createSession = () => apiClient.post<Envelope<{ session_id: string }>>('/client/chat/sessions', {}).then(unwrap)
export const getMessages = (id: string) => apiClient.get<Envelope<{ items: Message[] }>>(`/client/chat/sessions/${id}/messages`).then(unwrap)
export const sendMessage = (id: string, content: string) => apiClient.post<Envelope<Message>>(`/client/chat/sessions/${id}/messages`, { role: 'user', content }).then(unwrap)
export const registerEvent = (id: number) => apiClient.post<Envelope<unknown>>(`/client/events/${id}/register`, {}).then(unwrap)
export const cancelEvent = (id: number) => apiClient.delete<Envelope<unknown>>(`/client/events/${id}/register`).then(unwrap)
