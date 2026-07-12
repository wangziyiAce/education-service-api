import { AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export default function ErrorState({
  title = '加载失败',
  message = '请检查网络连接后重试。',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="text-center max-w-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="h-6 w-6 text-destructive" />
        </div>
        <h3 className="mt-4 text-sm font-medium text-foreground">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="mt-4">
            重试
          </Button>
        )}
      </div>
    </div>
  )
}
