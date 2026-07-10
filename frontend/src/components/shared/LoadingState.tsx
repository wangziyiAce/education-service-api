import { Skeleton } from '@/components/ui/skeleton'

interface LoadingStateProps {
  text?: string
  /** 是否显示骨架屏版式（含标题行+3行内容） */
  skeleton?: boolean
}

export default function LoadingState({ text = '加载中...', skeleton = true }: LoadingStateProps) {
  if (!skeleton) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="mt-3 text-sm text-muted-foreground">{text}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-64 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  )
}
