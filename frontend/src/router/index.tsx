/**
 * 首期路由配置。
 *
 * 路由结构：
 *   /login                        → 登录页（公开）
 *   /dashboard                    → 平台总览
 *   /reports                      → 报告列表
 *   /reports/generate             → 生成报告
 *   /reports/:id                  → 报告详情
 *   /reports/actions              → 行动项管理 (P1)
 *   /reports/schedules            → 定时计划 (P1)
 *   /customer-assessment          → 客户研判 [Beta]
 *   /customer-service             → 客服助手 [即将开放]
 *   /student-assistant            → 学生助手 [即将开放]
 *   /enterprise-assistant         → 企业助手 [即将开放]
 *   /*                            → 404
 *
 * 注意：不使用 React.lazy()，因为 React Router v7 的 createBrowserRouter
 * 会在路由切换时做自己的 Suspense 管理；外部 lazy() 会导致 DOM
 * reconciliation 冲突（insertBefore 错误）。
 * 页面代码量适中，直接 import 不影响性能。
 */

import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'
import AppShell from '@/components/layout/AppShell'

import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ReportListPage from '@/pages/reports/ReportListPage'
import ReportGeneratePage from '@/pages/reports/ReportGeneratePage'
import ReportDetailPage from '@/pages/reports/ReportDetailPage'
import ReportActionsPage from '@/pages/reports/ReportActionsPage'
import ReportSchedulesPage from '@/pages/reports/ReportSchedulesPage'
import FeatureUnavailablePage from '@/components/shared/FeatureUnavailablePage'
import NotFoundPage from '@/pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },

      // 智能报告中心（P0 核心）
      { path: 'reports', element: <ReportListPage /> },
      { path: 'reports/generate', element: <ReportGeneratePage /> },
      { path: 'reports/:id', element: <ReportDetailPage /> },
      { path: 'reports/actions', element: <ReportActionsPage /> },
      { path: 'reports/schedules', element: <ReportSchedulesPage /> },

      // 智能助手（P2：暂未开放）
      {
        path: 'customer-assessment',
        element: (
          <FeatureUnavailablePage
            feature="客户研判助手"
            status="beta"
            description="上传客户资料或输入背景信息，AI 自动匹配产品线并生成客户画像与风险提示。"
            plannedCapabilities={[
              '自然语言客户资料录入',
              'PDF / Excel 文件上传解析',
              '客户画像自动生成',
              '产品线匹配与评分',
              '风险提示与下一步建议',
            ]}
            integrationNote="后端为 V1 遗留能力，正在进行 API 接口验证和 Dify Chatflow 联调。"
          />
        ),
      },
      {
        path: 'customer-service',
        element: (
          <FeatureUnavailablePage
            feature="客服智能助手"
            status="coming_soon"
            description="基于 RAG 知识库的智能客服，支持公司业务咨询、留学政策查询、课程推荐和 FAQ。"
            plannedCapabilities={[
              '公司信息与业务咨询',
              '留学政策实时查询',
              '课程与项目推荐',
              '活动查询与报名',
              'FAQ 自动应答',
              '知识库引用来源展示',
            ]}
            integrationNote="正在建设 RAG 知识库和 Dify Chatflow 对话流程，预计下一阶段开放。"
          />
        ),
      },
      {
        path: 'student-assistant',
        element: (
          <FeatureUnavailablePage
            feature="学生智能助手"
            status="coming_soon"
            description="面向已签约学生的个人助手，支持请假、成绩查询、申请进度、签证追踪和生活支持。"
            plannedCapabilities={[
              '请假申请与进度查询',
              '成绩与考试信息查询',
              '论文截止日期提醒',
              '院校申请与签证进度',
              '海外生活与紧急求助',
              '情绪支持与人工介入',
            ]}
            integrationNote="正在设计学生数据权限、隐私边界和 Dify Chatflow，预计下一阶段开放。"
          />
        ),
      },
      {
        path: 'enterprise-assistant',
        element: (
          <FeatureUnavailablePage
            feature="企业智能助手"
            status="coming_soon"
            description="面向内部员工的企业运营助手，支持客户管理、日报提交、组织查询和审批流程。"
            plannedCapabilities={[
              '客户录入与状态更新',
              '跟进记录与日报结构化',
              '日报汇总与提交',
              '组织架构与新人指南',
              '请假/投诉待办与审批',
              '模板式只读数据查询',
            ]}
            integrationNote="正在设计写操作二次确认流程和数据权限体系，预计下一阶段开放。"
          />
        ),
      },

      // 错误页面
      { path: '403', element: <NotFoundPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
