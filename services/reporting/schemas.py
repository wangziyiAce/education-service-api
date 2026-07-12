"""智能报告 V2 的内容契约。

这里定义的是“报告内容本身”的结构，不是数据库 ORM。

为什么要每类报告独立 Schema？
-----------------------------
V1 把所有报告都塞进 ``summary/key_findings/risks/suggestions`` 四个字段，
前端不知道某类报告到底有哪些指标，也很难做精细化展示。

V2 改成：

* 外层 ``ReportEnvelope`` 统一描述任务状态、周期、触发来源、数据质量；
* 内层 ``report_content`` 按 ``report_type`` 使用独立 Pydantic 模型；
* 历史报告仍可用 ``schema_version=1`` 兼容查询；
* 新报告统一 ``schema_version=2``，方便 Swagger/OpenAPI 展示契约。
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


REPORT_SCHEMA_VERSION = 2


class DataQuality(BaseModel):
    """报告数据质量说明。

    ``level`` 用于前端展示整体可信度；
    ``warnings`` 记录可选数据源缺失、成本为 0、分母为 0 等情况；
    ``data_source`` 明确标记数据来源，避免开发 Mock 被误认为正式数据。
    """

    level: Literal["ok", "warning", "degraded", "empty", "failed"] = "ok"
    warnings: list[str] = Field(default_factory=list)
    data_source: Literal["database", "mock", "local", "mixed"] = "database"


class MetricTrace(BaseModel):
    """指标追溯信息。

    报告里重要数字都应能说明：
    来自哪些表、过滤条件是什么、计算公式是什么。
    """

    metric_name: str
    source_tables: list[str] = Field(default_factory=list)
    formula: Optional[str] = None
    filters: dict[str, Any] = Field(default_factory=dict)


class BaseReportContent(BaseModel):
    """所有报告内容共享的最小字段。"""

    summary: str = ""
    explanation: str = ""
    metric_traces: list[MetricTrace] = Field(default_factory=list)


class CustomerOpsContent(BaseReportContent):
    metrics: dict[str, Any] = Field(default_factory=dict)
    stage_distribution: list[dict[str, Any]] = Field(default_factory=list)
    stale_leads: list[dict[str, Any]] = Field(default_factory=list)
    churn_analysis: list[dict[str, Any]] = Field(default_factory=list)


class DailySummaryContent(BaseReportContent):
    metrics: dict[str, Any] = Field(default_factory=dict)
    key_progress: list[str] = Field(default_factory=list)
    common_risks: list[str] = Field(default_factory=list)
    next_plans: list[str] = Field(default_factory=list)


class WeeklySummaryContent(BaseReportContent):
    business_sections: dict[str, Any] = Field(default_factory=dict)
    cross_module_risks: list[str] = Field(default_factory=list)
    management_actions: list[str] = Field(default_factory=list)


class PsychWeeklyContent(BaseReportContent):
    metrics: dict[str, Any] = Field(default_factory=dict)
    emotion_trend: list[dict[str, Any]] = Field(default_factory=list)
    alert_status: list[dict[str, Any]] = Field(default_factory=list)
    processing_timeliness: dict[str, Any] = Field(default_factory=dict)


class ComplaintWeeklyContent(BaseReportContent):
    metrics: dict[str, Any] = Field(default_factory=dict)
    sla_summary: dict[str, Any] = Field(default_factory=dict)
    high_frequency_issues: list[dict[str, Any]] = Field(default_factory=list)


class ApplicationRiskMetrics(BaseModel):
    total_applications: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    overdue_count: int = 0
    missing_material_count: int = 0


class ApplicationRiskItem(BaseModel):
    application_id: int
    student_id: Optional[int] = None
    owner_id: Optional[int] = None
    stage: str = ""
    risk_score: int
    risk_level: Literal["high", "medium", "low"]
    risk_reasons: list[str] = Field(default_factory=list)
    missing_materials: list[str] = Field(default_factory=list)
    next_action: Optional[str] = None


class ReportActionSuggestion(BaseModel):
    owner_id: Optional[int] = None
    action: str
    due_date: Optional[str] = None
    priority: Literal["urgent", "high", "medium", "low"] = "medium"


class ApplicationRiskContent(BaseReportContent):
    metrics: ApplicationRiskMetrics = Field(default_factory=ApplicationRiskMetrics)
    risk_items: list[ApplicationRiskItem] = Field(default_factory=list)
    action_checklist: list[ReportActionSuggestion] = Field(default_factory=list)


class SalesFunnelContent(BaseReportContent):
    funnel_counts: dict[str, int] = Field(default_factory=dict)
    conversion_rates: dict[str, Optional[float]] = Field(default_factory=dict)
    avg_stage_stay_days: dict[str, Optional[float]] = Field(default_factory=dict)
    stalled_leads: list[dict[str, Any]] = Field(default_factory=list)
    consultant_performance: list[dict[str, Any]] = Field(default_factory=list)


class ChannelROIContent(BaseReportContent):
    channel_metrics: list[dict[str, Any]] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)


class ServiceSLAContent(BaseReportContent):
    sla_overview: dict[str, Any] = Field(default_factory=dict)
    complaint_sla: list[dict[str, Any]] = Field(default_factory=list)
    admin_service_sla: list[dict[str, Any]] = Field(default_factory=list)
    psych_alert_sla: list[dict[str, Any]] = Field(default_factory=list)
    backlog_aging: list[dict[str, Any]] = Field(default_factory=list)


class ActionClosureContent(BaseReportContent):
    metrics: dict[str, Any] = Field(default_factory=dict)
    overdue_actions: list[dict[str, Any]] = Field(default_factory=list)
    repeated_issues: list[dict[str, Any]] = Field(default_factory=list)
    target_achievement: list[dict[str, Any]] = Field(default_factory=list)


ReportContentUnion = Union[
    CustomerOpsContent,
    DailySummaryContent,
    WeeklySummaryContent,
    PsychWeeklyContent,
    ComplaintWeeklyContent,
    ApplicationRiskContent,
    SalesFunnelContent,
    ChannelROIContent,
    ServiceSLAContent,
    ActionClosureContent,
    dict[str, Any],  # V1 历史报告兼容：旧结构不强制升级。
]


REPORT_CONTENT_MODELS: dict[str, type[BaseReportContent]] = {
    "customer_ops": CustomerOpsContent,
    "daily_summary": DailySummaryContent,
    "weekly_summary": WeeklySummaryContent,
    "psych_weekly": PsychWeeklyContent,
    "complaint_weekly": ComplaintWeeklyContent,
    "application_risk": ApplicationRiskContent,
    "sales_funnel": SalesFunnelContent,
    "channel_roi": ChannelROIContent,
    "service_sla": ServiceSLAContent,
    "action_closure": ActionClosureContent,
}


class ReportEnvelope(BaseModel):
    """报告详情接口返回的统一外壳。

    ``report_content`` 会根据 ``report_type + schema_version`` 自动转成对应
    的 Pydantic 模型。这个设计能让前端通过类型选择渲染器，也能让 Swagger
    看到每类报告的内容结构。
    """

    id: int
    report_type: str
    title: str
    period: dict[str, Any]
    status: Literal["pending", "generating", "completed", "failed"]
    schema_version: int = REPORT_SCHEMA_VERSION
    data_quality: DataQuality | dict[str, Any] = Field(default_factory=DataQuality)
    trigger_source: Literal["manual", "schedule", "retry", "system"] = "manual"
    generated_by: Optional[int] = None
    report_content: ReportContentUnion = Field(default_factory=dict)

    @field_validator("data_quality", mode="before")
    @classmethod
    def normalize_data_quality(cls, value: Any) -> DataQuality | dict[str, Any]:
        if value is None:
            return DataQuality()
        return value

    @model_validator(mode="after")
    def cast_type_specific_content(self) -> "ReportEnvelope":
        """把 report_content 转成对应报告类型的独立模型。

        V1 旧数据保持 dict，不做强制迁移；V2 新数据必须按注册模型校验。
        """

        if self.schema_version < REPORT_SCHEMA_VERSION:
            return self

        model = REPORT_CONTENT_MODELS.get(self.report_type)
        if model and isinstance(self.report_content, dict):
            self.report_content = model.model_validate(self.report_content)
        return self

