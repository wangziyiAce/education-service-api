import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: { requiresAuth: false, title: '登录' },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/login/RegisterView.vue'),
      meta: { requiresAuth: false, title: '注册' },
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '首页看板', requiresAuth: true },
        },
        {
          path: 'courses',
          name: 'Courses',
          component: () => import('@/views/courses/CourseListView.vue'),
          meta: { title: '课程管理', requiresAuth: true },
        },
        {
          path: 'courses/:id',
          name: 'CourseDetail',
          component: () => import('@/views/courses/CourseDetailView.vue'),
          meta: { title: '课程详情', requiresAuth: true },
        },
        {
          path: 'events',
          name: 'Events',
          component: () => import('@/views/events/EventListView.vue'),
          meta: { title: '活动管理', requiresAuth: true },
        },
        {
          path: 'events/:id',
          name: 'EventDetail',
          component: () => import('@/views/events/EventDetailView.vue'),
          meta: { title: '活动详情', requiresAuth: true },
        },
        {
          path: 'crm/leads',
          name: 'Leads',
          component: () => import('@/views/crm/LeadListView.vue'),
          meta: { title: '客户列表', requiresAuth: true },
        },
        {
          path: 'crm/leads/create',
          name: 'LeadCreate',
          component: () => import('@/views/crm/LeadCreateView.vue'),
          meta: { title: '新增客户', requiresAuth: true },
        },
        {
          path: 'crm/leads/:id',
          name: 'LeadDetail',
          component: () => import('@/views/crm/LeadDetailView.vue'),
          meta: { title: '客户详情', requiresAuth: true },
        },
        {
          path: 'assistant',
          name: 'Assistant',
          component: () => import('@/views/assistant/AssistantChatView.vue'),
          meta: { title: '智能助手', requiresAuth: true },
        },
        {
          path: 'student/leaves',
          name: 'Leaves',
          component: () => import('@/views/student/LeaveListView.vue'),
          meta: { title: '请假管理', requiresAuth: true },
        },
        {
          path: 'student/feedbacks',
          name: 'Feedbacks',
          component: () => import('@/views/student/FeedbackListView.vue'),
          meta: { title: '投诉管理', requiresAuth: true },
        },
        {
          path: 'student/psych-alerts',
          name: 'PsychAlerts',
          component: () => import('@/views/student/PsychAlertView.vue'),
          meta: { title: '心理预警', requiresAuth: true },
        },
        {
          path: 'profile/upload',
          name: 'ProfileUpload',
          component: () => import('@/views/profile/ProfileUploadView.vue'),
          meta: { title: '客户研判', requiresAuth: true },
        },
        {
          path: 'reports',
          name: 'Reports',
          component: () => import('@/views/report/ReportListView.vue'),
          meta: { title: '报告中心', requiresAuth: true },
        },
        {
          path: 'reports/assistant',
          name: 'ReportAssistant',
          component: () => import('@/views/report/ReportAssistantView.vue'),
          meta: { title: '报告助手', requiresAuth: true },
        },
        {
          path: 'reports/data',
          name: 'ReportData',
          component: () => import('@/views/report/ReportDataView.vue'),
          meta: { title: '报告数据', requiresAuth: true },
        },
        {
          path: 'reports/schedules',
          name: 'ReportSchedules',
          component: () => import('@/views/report/ReportScheduleView.vue'),
          meta: { title: '报告调度', requiresAuth: true },
        },
        {
          path: 'reports/:id',
          name: 'ReportDetail',
          component: () => import('@/views/report/ReportDetailView.vue'),
          meta: { title: '报告详情', requiresAuth: true },
        },
        {
          path: 'chat',
          name: 'CustomerChat',
          component: () => import('@/views/customer/CustomerChatView.vue'),
          meta: { title: '智能客服', requiresAuth: true },
        },
        {
          path: 'student-assistant',
          name: 'StudentAssistant',
          component: () => import('@/views/student/StudentAssistantView.vue'),
          meta: { title: '学生智能助手', requiresAuth: true },
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/profile/ProfileView.vue'),
          meta: { title: '个人信息', requiresAuth: true },
        },
        {
          path: 'admin/users',
          name: 'UserManagement',
          component: () => import('@/views/admin/UserManagementView.vue'),
          meta: { title: '用户管理', requiresAuth: true },
        },
      ],
    },
    {
      path: '/403',
      name: 'Forbidden',
      component: () => import('@/views/error/ForbiddenView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFoundView.vue'),
    },
  ],
})

// 全局路由守卫
router.beforeEach(async (to, _from) => {
  const auth = useAuthStore()

  // 不需要登录的页面直接放行
  if (to.meta.requiresAuth === false) {
    return true
  }

  // 需要登录但未登录 → 跳转登录页
  if (!auth.isLoggedIn) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      return '/login'
    }
    // 有 token 但 Store 未初始化 → 等待恢复完成（页面刷新场景）
    try {
      await auth.restoreFromToken()
      return true
    } catch {
      return '/login'
    }
  }

  return true
})

export default router
