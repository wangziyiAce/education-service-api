/** 状态标签映射表 — 将后端 ENUM 值转为前端展示的中文和 Element Plus Tag 颜色 */
export const STATUS_MAP: Record<string, Record<string, { label: string; color: string }>> = {
  lead: {
    new:        { label: '新线索',   color: 'info' },
    contacting: { label: '跟进中',   color: 'warning' },
    qualified:  { label: '已确认',   color: 'success' },
    signed:     { label: '已签约',   color: '' },
    lost:       { label: '已流失',   color: 'danger' },
  },
  event: {
    upcoming:   { label: '即将开始', color: 'primary' },
    ongoing:    { label: '进行中',   color: 'success' },
    ended:      { label: '已结束',   color: 'info' },
    cancelled:  { label: '已取消',   color: 'danger' },
  },
  leave: {
    pending:    { label: '待审批',   color: 'warning' },
    approved:   { label: '已通过',   color: 'success' },
    rejected:   { label: '已驳回',   color: 'danger' },
    cancelled:  { label: '已撤销',   color: 'info' },
  },
  feedback: {
    pending:    { label: '待处理',   color: 'warning' },
    processing: { label: '处理中',   color: 'primary' },
    resolved:   { label: '已解决',   color: 'success' },
  },
  psych: {
    low:        { label: '低风险',   color: 'success' },
    medium:     { label: '中风险',   color: 'warning' },
    high:       { label: '高风险',   color: 'danger' },
  },
  report: {
    generating: { label: '生成中',   color: 'warning' },
    completed:  { label: '已完成',   color: 'success' },
    failed:     { label: '失败',     color: 'danger' },
  },
  course: {
    '1': { label: '上架', color: 'success' },
    '0': { label: '下架', color: 'info' },
  },
}

/** 客户状态流转规则 */
export const LEAD_STATUS_TRANSITIONS: Record<string, string[]> = {
  new:        ['contacting', 'lost'],
  contacting: ['qualified', 'lost'],
  qualified:  ['signed', 'lost'],
  signed:     [],
  lost:       ['contacting'],
}

/** 用户类型中文映射 */
export const USER_TYPE_MAP: Record<string, string> = {
  student:  '学生',
  employee: '员工',
  admin:    '管理员',
  visitor:  '访客',
}
