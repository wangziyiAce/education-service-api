/**
 * TanStack Query Client 配置。
 *
 * 集中管理所有 API 数据请求的缓存策略、重试逻辑和 stale 时间。
 * 页面组件通过 useQuery/useMutation hooks 使用此 queryClient。
 */

import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /** 请求失败时重试 1 次 */
      retry: 1,
      /** 数据视为新鲜的时间（5 分钟），此期间不重新请求 */
      staleTime: 5 * 60 * 1000,
      /** 窗口重新获得焦点时不自动重新请求 */
      refetchOnWindowFocus: false,
    },
    mutations: {
      /** 变更操作不重试 */
      retry: 0,
    },
  },
})
