import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'
import { getDefaultRoute } from '@/lib/role-navigation'
export default function RoleLanding() { return <Navigate to={getDefaultRoute(useAuthStore((s) => s.user?.role_code))} replace /> }
