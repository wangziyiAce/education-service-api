"""智能报告类型注册表。

注册表解决的问题：
----------------
如果每新增一种报告都去改一堆 ``if report_type == ...``，项目很快会变成
难维护的分支地狱。注册表把“报告类型 -> 聚合器、Schema、模板、权限、默认周期”
集中登记，编排层只需要根据 report_type 查定义即可。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from services.reporting.schemas import REPORT_CONTENT_MODELS, REPORT_SCHEMA_VERSION


AggregatorName = str


@dataclass(frozen=True)
class ReportDefinition:
    """单个报告类型的元数据定义。

    Attributes:
        report_type: 程序内部使用的报告类型编码。
        label: 给前端和 Swagger 展示的中文名。
        schema_version: 当前内容结构版本，V2 固定为 2。
        content_model: 该报告的 Pydantic 内容模型。
        aggregator_name: 聚合器函数名。这里用字符串避免注册表导入聚合器导致循环依赖。
        template_name: 后端 HTML 模板名。
        allowed_roles: 允许生成/查看该管理报告的角色。
        default_period_rule: 定时任务默认统计周期。
        available_filters: 前端可展示的筛选条件。
    """

    report_type: str
    label: str
    schema_version: int
    content_model: type
    aggregator_name: AggregatorName
    template_name: str
    allowed_roles: tuple[str, ...]
    default_period_rule: str
    available_filters: tuple[str, ...] = ()


MANAGEMENT_ROLES = ("admin", "manager", "employee", "team_leader")
ADMIN_MANAGER_ROLES = ("admin", "manager")


def _definition(
    report_type: str,
    label: str,
    aggregator_name: str,
    template_name: Optional[str] = None,
    allowed_roles: tuple[str, ...] = MANAGEMENT_ROLES,
    default_period_rule: str = "previous_week",
    available_filters: tuple[str, ...] = (),
) -> ReportDefinition:
    return ReportDefinition(
        report_type=report_type,
        label=label,
        schema_version=REPORT_SCHEMA_VERSION,
        content_model=REPORT_CONTENT_MODELS[report_type],
        aggregator_name=aggregator_name,
        template_name=template_name or f"{report_type}.html",
        allowed_roles=allowed_roles,
        default_period_rule=default_period_rule,
        available_filters=available_filters,
    )


REPORT_REGISTRY: dict[str, ReportDefinition] = {
    # 原有 5 类：保留类型编码，升级内容结构和指标口径。
    "customer_ops": _definition(
        "customer_ops",
        "客户经营分析报告",
        "aggregate_customer_ops",
        available_filters=("owner_id", "department", "source_channel"),
    ),
    "daily_summary": _definition(
        "daily_summary",
        "员工日报汇总报告",
        "aggregate_daily_summary",
        default_period_rule="previous_day",
        available_filters=("employee_id", "department"),
    ),
    "weekly_summary": _definition(
        "weekly_summary",
        "综合经营周报",
        "aggregate_weekly_summary",
        allowed_roles=ADMIN_MANAGER_ROLES,
        available_filters=("department",),
    ),
    "psych_weekly": _definition(
        "psych_weekly",
        "学生心理预警周报",
        "aggregate_psych_weekly",
        allowed_roles=("admin", "manager", "team_leader"),
        available_filters=("student_id", "risk_level", "status"),
    ),
    "complaint_weekly": _definition(
        "complaint_weekly",
        "投诉处理周报",
        "aggregate_complaint_weekly",
        available_filters=("priority", "category", "status"),
    ),
    # 新增 5 类：从申请风险、服务 SLA 这些高价值管理场景开始建设。
    "application_risk": _definition(
        "application_risk",
        "申请风险报告",
        "aggregate_application_risk",
        available_filters=("student_id", "owner_id", "stage", "risk_level"),
    ),
    "sales_funnel": _definition(
        "sales_funnel",
        "销售漏斗报告",
        "aggregate_sales_funnel",
        available_filters=("owner_id", "department", "source_channel", "cohort"),
    ),
    "channel_roi": _definition(
        "channel_roi",
        "渠道 ROI 报告",
        "aggregate_channel_roi",
        allowed_roles=ADMIN_MANAGER_ROLES,
        available_filters=("channel", "campaign"),
    ),
    "service_sla": _definition(
        "service_sla",
        "服务 SLA 报告",
        "aggregate_service_sla",
        available_filters=("service_type", "priority", "owner_id"),
    ),
    "action_closure": _definition(
        "action_closure",
        "报告行动闭环报告",
        "aggregate_action_closure",
        allowed_roles=ADMIN_MANAGER_ROLES,
        available_filters=("owner_id", "status", "risk_code"),
    ),
}


def get_report_definition(report_type: str) -> ReportDefinition:
    """按报告类型获取定义；不存在时抛出明确异常，方便 API 返回 400。"""

    try:
        return REPORT_REGISTRY[report_type]
    except KeyError as exc:
        raise ValueError(f"不支持的报告类型: {report_type}") from exc


def list_report_types() -> list[ReportDefinition]:
    """返回全部报告类型定义，供 ``GET /api/v1/reports/types`` 使用。"""

    return list(REPORT_REGISTRY.values())

