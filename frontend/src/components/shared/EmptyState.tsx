import { FileText } from 'lucide-react'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: React.ReactNode
  action?: React.ReactNode
}

export default function EmptyState({
  title = '暂无数据',
  description = '当前没有可显示的内容。',
  icon,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="text-center max-w-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          {icon || <FileText className="h-6 w-6 text-muted-foreground" />}
        </div>
        <h3 className="mt-4 text-sm font-medium text-foreground">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        {action && <div className="mt-4">{action}</div>}
      </div>
    </div>
  )
}
