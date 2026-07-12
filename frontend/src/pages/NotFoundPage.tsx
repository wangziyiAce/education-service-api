/**
 * 404 / 403 错误页面。
 */

import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Home, ArrowLeft } from 'lucide-react'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <p className="text-8xl font-bold text-muted-foreground/30">404</p>
        <h1 className="mt-4 text-xl font-semibold text-foreground">页面不存在</h1>
        <p className="mt-2 text-sm text-muted-foreground">您访问的页面可能已被移除或地址有误。</p>
        <div className="mt-6 flex justify-center gap-3">
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回上一页
          </Button>
          <Button onClick={() => navigate('/dashboard')}>
            <Home className="mr-2 h-4 w-4" />
            返回工作台
          </Button>
        </div>
      </div>
    </div>
  )
}
