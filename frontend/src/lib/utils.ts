/**
 * shadcn/ui 工具函数。
 *
 * 使用 clsx 合并类名 + tailwind-merge 智能去重冲突的 Tailwind 类。
 * 避免多个组件组合时出现样式覆盖问题。
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
