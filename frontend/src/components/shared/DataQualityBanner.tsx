/**
 * 数据质量提示横幅。
 *
 * 根据后端返回的 data_quality.level 显示不同颜色的提示条。
 * 对齐后端 DataQuality 模型：
 *   ok → 绿色（数据正常）
 *   warning → 橙色（有警告）
 *   degraded → 红色（数据降级）
 *   empty → 灰色（无数据）
 *   failed → 红色（数据失败）
 */

import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, CheckCircle2, AlertTriangle, Database } from 'lucide-react'
import type { DataQuality } from '@/types/common'

const LEVEL_CONFIG: Record<string, { icon: React.ComponentType<{ className?: string }>; variant: 'default' | 'destructive' | 'warning'; label: string }> = {
  ok: { icon: CheckCircle2, variant: 'default', label: '数据正常' },
  warning: { icon: AlertTriangle, variant: 'warning', label: '数据有警告' },
  degraded: { icon: AlertCircle, variant: 'destructive', label: '数据降级' },
  empty: { icon: Database, variant: 'default', label: '暂无数据' },
  failed: { icon: AlertCircle, variant: 'destructive', label: '数据获取失败' },
}

interface DataQualityBannerProps {
  dataQuality?: DataQuality | null
}

export default function DataQualityBanner({ dataQuality }: DataQualityBannerProps) {
  if (!dataQuality) return null

  const config = LEVEL_CONFIG[dataQuality.level] || LEVEL_CONFIG.ok
  const Icon = config.icon

  // 数据正常时不显示横幅
  if (dataQuality.level === 'ok' && dataQuality.warnings.length === 0) {
    return null
  }

  return (
    <Alert variant={config.variant} className="mb-4">
      <Icon className="h-4 w-4" />
      <AlertDescription>
        <span className="font-medium">{config.label}</span>
        {dataQuality.warnings.length > 0 && (
          <ul className="mt-1 list-disc list-inside text-xs">
            {dataQuality.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        )}
        {dataQuality.data_source === 'mock' && (
          <span className="ml-2 inline-flex items-center rounded bg-warning/20 px-1.5 py-0.5 text-[10px] font-medium text-warning">
            演示数据
          </span>
        )}
      </AlertDescription>
    </Alert>
  )
}
