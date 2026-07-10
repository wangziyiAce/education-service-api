/**
 * 认证相关 API。
 *
 * 对应后端 routers/auth.py:
 *   - POST /api/v1/auth/login
 *   - GET  /api/v1/auth/me
 */

import apiClient from '@/lib/api-client'
import type { LoginRequest, TokenResponse, CurrentUser } from '@/types/auth'

/** 用户登录，返回 JWT Token 和用户信息 */
export function login(data: LoginRequest) {
  return apiClient.post<TokenResponse>('/auth/login', data)
}

/** 获取当前登录用户信息 */
export function getMe() {
  return apiClient.get<CurrentUser>('/auth/me')
}
