# 智能报告模块 V2 前端对接与 Dify 契约

## 1. 前端对接原则

前端不需要判断报告数字怎么算，只需要按以下规则渲染：

- 先调用 `GET /api/v1/reports/types` 获取 10 类报告的 `report_type`、`schema_version`、权限和过滤条件。
- 生成报告调用 `POST /api/v1/reports/generate`，接口返回 `202` 和报告任务 ID。
- 前端轮询 `GET /api/v1/reports/{id}`，直到 `status=completed/failed`。
- 渲染时根据 `report_type + schema_version` 选择对应页面组件。
- `schema_version=1` 按历史通用结构兼容；`schema_version=2` 按独立内容结构渲染。

## 2. 核心接口

| 功能 | 方法 | 路径 |
|---|---|---|
| 登录 | POST | `/api/v1/auth/login` |
| 当前用户 | GET | `/api/v1/auth/me` |
| 报告类型 | GET | `/api/v1/reports/types` |
| 生成报告 | POST | `/api/v1/reports/generate` |
| 报告列表 | GET | `/api/v1/reports` |
| 报告详情 | GET | `/api/v1/reports/{id}` |
| 失败重试 | POST | `/api/v1/reports/{id}/retry` |
| 报告计划 | CRUD | `/api/v1/report-schedules` |
| 报告行动 | POST/GET | `/api/v1/reports/{id}/actions` |
| 行动详情 | GET/PATCH | `/api/v1/report-actions/{id}` |
| 事实数据维护 | POST/GET | `/api/v1/report-data/*` |

## 3. Dify Workflow 输入契约

统一 Workflow 输入：

```json
{
  "report_type": "application_risk",
  "schema_version": 2,
  "report_title": "申请风险周报",
  "period": {"start": "2026-07-01", "end": "2026-07-07"},
  "aggregated_data": {},
  "expected_schema": {},
  "data_quality": {"level": "ok", "warnings": [], "data_source": "database"}
}
```

## 4. Dify 输出边界

Dify 只能补充解释性字段：

- `summary`
- `explanation`

业务数字必须以 `aggregated_data` 为准，不允许 Dify 改写：

- 风险分
- 转化率
- CPL / CAC / ROI
- SLA 超时
- 行动完成率

如果 Dify 第一次输出不符合 Schema，后端会携带校验错误重试一次；第二次仍失败，报告任务进入 `failed`。

## 5. 隐私边界

心理相关报告禁止输出：

- 学生心理咨询原文；
- 诊断性语言；
- 可识别学生隐私的长文本。

心理报告只允许输出：

- 风险等级分布；
- 预警状态；
- 首次跟进时效；
- 趋势性统计。

## 6. 面试表达

可以这样讲：

> 我把智能报告模块做成“数据聚合 + 规则计算 + AI 解释 + 后端模板渲染”的链路。所有业务数字都来自 SQL 和规则引擎，Dify 只负责把结果解释成人能看懂的管理建议。这样既能发挥大模型的表达能力，也能避免大模型编造指标。

