import { createBrowserRouter } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'
import RoleRoute from './RoleRoute'
import RoleLanding from './RoleLanding'
import AppShell from '@/components/layout/AppShell'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import CustomerServicePage from '@/pages/CustomerServicePage'
import StudentPortalPage from '@/pages/StudentPortalPage'
import UserManagementPage from '@/pages/admin/UserManagementPage'
import ReportListPage from '@/pages/reports/ReportListPage'
import ReportGeneratePage from '@/pages/reports/ReportGeneratePage'
import ReportDetailPage from '@/pages/reports/ReportDetailPage'
import ReportActionsPage from '@/pages/reports/ReportActionsPage'
import ReportSchedulesPage from '@/pages/reports/ReportSchedulesPage'
import FeatureUnavailablePage from '@/components/shared/FeatureUnavailablePage'
import NotFoundPage from '@/pages/NotFoundPage'
import { managementRoles, staffRoles } from '@/lib/role-navigation'

const enterprise=<FeatureUnavailablePage feature="企业运营" status="coming_soon" description="面向员工的运营工作区。" plannedCapabilities={['客户管理','跟进记录','日报提交']} integrationNote="现有接口保持不变，业务页后续深化。" />
const assessment=<FeatureUnavailablePage feature="客户研判" status="beta" description="客户资料与产品匹配工作区。" plannedCapabilities={['资料录入','画像研判','风险提示']} integrationNote="沿用现有后端能力。" />
export const router=createBrowserRouter([{path:'/login',element:<LoginPage/>},{path:'/',element:<ProtectedRoute><AppShell/></ProtectedRoute>,children:[{index:true,element:<RoleLanding/>},{path:'dashboard',element:<RoleRoute allow={managementRoles}><DashboardPage/></RoleRoute>},{path:'customer-service',element:<CustomerServicePage/>},{path:'student-assistant',element:<StudentPortalPage/>},{path:'enterprise-assistant',element:<RoleRoute allow={staffRoles}>{enterprise}</RoleRoute>},{path:'customer-assessment',element:<RoleRoute allow={staffRoles}>{assessment}</RoleRoute>},{path:'reports',element:<RoleRoute allow={managementRoles}><ReportListPage/></RoleRoute>},{path:'reports/generate',element:<RoleRoute allow={managementRoles}><ReportGeneratePage/></RoleRoute>},{path:'reports/actions',element:<RoleRoute allow={managementRoles}><ReportActionsPage/></RoleRoute>},{path:'reports/schedules',element:<RoleRoute allow={managementRoles}><ReportSchedulesPage/></RoleRoute>},{path:'reports/:id',element:<RoleRoute allow={managementRoles}><ReportDetailPage/></RoleRoute>},{path:'admin/users',element:<RoleRoute allow={managementRoles}><UserManagementPage/></RoleRoute>},{path:'403',element:<NotFoundPage/>},{path:'*',element:<NotFoundPage/>}]}])
