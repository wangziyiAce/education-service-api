/**
 * 页面标题栏组件。
 *
 * 职责：统一管理所有页面顶部的标题、描述和操作按钮区域。
 */

import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: string
  children?: React.ReactNode
  className?: string
}

export default function PageHeader({ title, description, children, className }: PageHeaderProps) {
  return (
    <div className={cn('mb-6 flex items-start justify-between', className)}>
      <div>
        <h1 className="text-xl font-bold text-foreground">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </div>
  )
}
