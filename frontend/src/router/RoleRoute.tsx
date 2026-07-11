import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'
export default function RoleRoute({ allow, children }: { allow: string[]; children: React.ReactNode }) { const role = useAuthStore((s) => s.user?.role_code); return role && allow.includes(role) ? children : <Navigate to="/403" replace /> }
