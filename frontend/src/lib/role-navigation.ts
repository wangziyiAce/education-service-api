import { ROLE_CODES } from '@/types/auth'

export const defaultRoutes: Record<string, string> = {
  admin: '/dashboard',
  manager: '/dashboard',
  employee: '/enterprise-assistant',
  team_leader: '/enterprise-assistant',
  student: '/student-assistant',
}

/** 未知角色进入最小权限学生门户，避免意外落入管理首页。 */
export function getDefaultRoute(role?: string | null) { return defaultRoutes[role || ''] || '/student-assistant' }

export const managementRoles = [ROLE_CODES.ADMIN, ROLE_CODES.MANAGER]
export const staffRoles = [ROLE_CODES.ADMIN, ROLE_CODES.MANAGER, ROLE_CODES.EMPLOYEE, ROLE_CODES.TEAM_LEADER]
