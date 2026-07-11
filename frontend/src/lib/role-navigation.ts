export const defaultRoutes: Record<string, string> = { admin: '/dashboard', manager: '/dashboard', employee: '/enterprise-assistant', team_leader: '/enterprise-assistant', student: '/student-assistant' }
export const managementRoles = ['admin', 'manager']
export const staffRoles = ['admin', 'manager', 'employee', 'team_leader']
export function getDefaultRoute(role?: string | null) { return defaultRoutes[role || ''] || '/student-assistant' }
