import request from './request'
import type { LoginRequest, LoginResponse, UserInfo, UserCreate, UserUpdate, PasswordChangeRequest, RoleInfo, OrganizationInfo } from '@/types/auth'
import type { PaginatedData } from '@/types/api'

export const authApi = {
  login: (data: LoginRequest): Promise<LoginResponse> =>
    request.post('/auth/login', data),

  register: (data: { username: string; password: string; real_name?: string }): Promise<any> =>
    request.post('/auth/register', data),

  getMe: (): Promise<UserInfo> =>
    request.get('/auth/me'),

  listUsers: (params?: Record<string, any>): Promise<PaginatedData<UserInfo>> =>
    request.get('/auth/users', { params }),

  createUser: (data: UserCreate): Promise<UserInfo> =>
    request.post('/auth/users', data),

  getUser: (userId: number): Promise<UserInfo> =>
    request.get(`/auth/users/${userId}`),

  updateUser: (userId: number, data: UserUpdate): Promise<UserInfo> =>
    request.put(`/auth/users/${userId}`, data),

  changePassword: (userId: number, data: PasswordChangeRequest): Promise<void> =>
    request.put(`/auth/users/${userId}/password`, data),

  resetPassword: (userId: number, newPassword: string): Promise<void> =>
    request.put(`/auth/users/${userId}/reset-password`, { new_password: newPassword }),

  listRoles: (): Promise<RoleInfo[]> =>
    request.get('/auth/roles'),

  listOrganizations: (): Promise<OrganizationInfo[]> =>
    request.get('/auth/organizations'),

  getOrganizationTree: (): Promise<OrganizationInfo[]> =>
    request.get('/auth/organizations/tree'),

  createOrganization: (data: { org_name: string; parent_id?: number }): Promise<OrganizationInfo> =>
    request.post('/auth/organizations', data),
}
