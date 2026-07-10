/**
 * 通用 TypeScript 类型定义。
 *
 * 对齐后端 FastAPI 的通用响应结构，用于分页、筛选和状态标记。
 * 这些类型不依赖具体业务，被所有 API 模块复用。
 */

/** 分页请求参数 */
export interface PaginationParams {
  page: number
  page_size: number
}

/** 分页响应结构（对齐后端 ReportListResponse） */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 数据质量标记（对齐后端 DataQuality） */
export interface DataQuality {
  /** 质量等级：ok=正常, warning=有警告, degraded=降级, empty=无数据, failed=失败 */
  level: 'ok' | 'warning' | 'degraded' | 'empty' | 'failed'
  /** 具体警告信息列表 */
  warnings: string[]
  /** 数据来源：database=真实数据, mock=演示数据, local=本地模式, mixed=混合 */
  data_source: 'database' | 'mock' | 'local' | 'mixed'
}

/** 报告生成状态枚举 */
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed'

/** 报告触发来源 */
export type TriggerSource = 'manual' | 'schedule' | 'retry' | 'system'

/** API 对接状态（内部工程标记，非用户可见） */
export type APIIntegrationStatus = 'REAL' | 'MOCK' | 'PENDING' | 'NOT_TESTED'

/** 功能开放状态（用户可见） */
export type FeatureStatus = 'available' | 'beta' | 'coming_soon' | 'testing'

/** 功能未开放页面的配置数据 */
export interface FeatureConfig {
  feature: string
  icon: string
  status: 'beta' | 'coming_soon' | 'testing'
  description: string
  plannedCapabilities: string[]
  integrationNote: string
}
