/**
 * 主应用布局壳组件。
 *
 * 职责：
 * 1. 组合 Sidebar（左侧导航） + TopHeader（顶部栏） + 内容区
 * 2. 通过 <Outlet /> 渲染子路由页面
 *
 * 注意：不对 <Outlet /> 做额外的 Suspense 包裹。
 * React Router v7 的 createBrowserRouter 已内置路由级别的
 * suspense 管理，外部再包一层会导致 DOM reconciliation 冲突
 * （insertBefore 错误）。
 */

import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopHeader from './TopHeader'

export default function AppShell() {
  return (
    <div className="flex min-h-screen">
      {/* 左侧导航栏 */}
      <Sidebar />

      {/* 右侧主区域 */}
      <div className="ml-56 flex flex-1 flex-col">
        {/* 顶部栏 */}
        <TopHeader />

        {/* 内容工作区 */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
