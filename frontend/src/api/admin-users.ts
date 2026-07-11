import apiClient from '@/lib/api-client'
type Envelope<T> = { code: number; message: string; data: T }
export interface Role { id: number; role_code: string; role_name: string }
export interface User { id: number; username: string; real_name: string; user_type: string; status: string }
const unwrap = <T>(r: { data: Envelope<T> }) => r.data.data
export const getRoles = () => apiClient.get<Envelope<{ items: Role[] }>>('/auth/roles').then(unwrap)
export const getUsers = () => apiClient.get<Envelope<{ items: User[] }>>('/auth/users').then(unwrap)
export const createUser = (data: { username: string; password: string; real_name: string; user_type: string; role_id: number }) => apiClient.post<Envelope<User>>('/auth/users', data).then(unwrap)
