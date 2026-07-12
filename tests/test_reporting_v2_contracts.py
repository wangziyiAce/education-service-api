from datetime import date, datetime
from decimal import Decimal

from schemas.report import (
    ApplicationMaterialCreate,
    ChannelCostCreate,
    CRMLeadStatusUpdate,
    CustomerPaymentCreate,
    ReportActionCreate,
    ReportGenerateRequest,
)
from services.reporting.registry import REPORT_REGISTRY, get_report_definition
from services.reporting.schemas import REPORT_SCHEMA_VERSION, ReportEnvelope


EXPECTED_REPORT_TYPES = {
    "customer_ops",
    "daily_summary",
    "weekly_summary",
    "psych_weekly",
    "complaint_weekly",
    "application_risk",
    "sales_funnel",
    "channel_roi",
    "service_sla",
    "action_closure",
}


def test_registry_contains_ten_report_types_with_v2_schema():
    assert set(REPORT_REGISTRY.keys()) == EXPECTED_REPORT_TYPES
    assert all(definition.schema_version == REPORT_SCHEMA_VERSION for definition in REPORT_REGISTRY.values())


def test_registry_defines_permissions_templates_and_default_periods():
    definition = get_report_definition("application_risk")

    assert definition.report_type == "application_risk"
    assert "admin" in definition.allowed_roles
    assert definition.template_name.endswith(".html")
    assert definition.default_period_rule == "previous_week"


def test_report_envelope_accepts_type_specific_content():
    envelope = ReportEnvelope(
        id=1,
        report_type="application_risk",
        title="申请风险周报",
        period={"start": "2026-07-01", "end": "2026-07-07"},
        status="completed",
        schema_version=REPORT_SCHEMA_VERSION,
        data_quality={"level": "ok", "warnings": []},
        trigger_source="manual",
        generated_by=1,
        report_content={
            "summary": "本周共有 1 个高风险申请。",
            "metrics": {
                "total_applications": 1,
                "high_risk_count": 1,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "overdue_count": 1,
                "missing_material_count": 2,
            },
            "risk_items": [
                {
                    "application_id": 10,
                    "student_id": 100,
                    "owner_id": 3,
                    "stage": "material_preparation",
                    "risk_score": 90,
                    "risk_level": "high",
                    "risk_reasons": ["overdue"],
                    "missing_materials": ["PS", "推荐信"],
                    "next_action": "补齐材料并联系学生确认",
                }
            ],
            "action_checklist": [
                {
                    "owner_id": 3,
                    "action": "补齐申请材料",
                    "due_date": "2026-07-10",
                    "priority": "high",
                }
            ],
            "explanation": "所有风险分由规则引擎计算，AI 只负责解释。",
        },
    )

    assert envelope.report_content.metrics.high_risk_count == 1


def test_api_request_schemas_accept_frontend_friendly_aliases():
    """前端对接时更常传短字段名；后端 Schema 要负责把它们归一化为内部字段。

    这类测试看起来小，但价值很高：它保护的是“接口契约稳定性”。
    面试时可以说：智能报告模块不是只把接口写出来，还专门用测试保证
    前端契约、数据库字段和服务层字段之间不会因为命名差异而断链。
    """

    report_request = ReportGenerateRequest.model_validate(
        {
            "report_type": "application_risk",
            "title": "申请风险日报",
            "period_start": "2026-07-01",
            "period_end": "2026-07-09",
        }
    )
    assert report_request.report_title == "申请风险日报"

    action_request = ReportActionCreate.model_validate(
        {
            "suggestion": "补齐 Personal Statement 初稿",
            "risk_code": "APPLICATION_MATERIAL_MISSING",
        }
    )
    assert action_request.suggestion_text == "补齐 Personal Statement 初稿"

    material_request = ApplicationMaterialCreate.model_validate(
        {
            "application_id": 1001,
            "material_name": "Personal Statement",
            "is_required": True,
        }
    )
    assert material_request.required == 1

    channel_cost_request = ChannelCostCreate.model_validate(
        {
            "channel": "抖音",
            "spend_date": "2026-07-09",
            "cost": "1200.00",
        }
    )
    assert channel_cost_request.cost_date == date(2026, 7, 9)
    assert channel_cost_request.cost_amount == Decimal("1200.00")

    payment_request = CustomerPaymentCreate.model_validate(
        {
            "contract_id": 1,
            "payment_amount": "10000.00",
            "paid_time": "2026-07-09T12:30:00",
        }
    )
    assert payment_request.payment_time == datetime(2026, 7, 9, 12, 30)

    crm_request = CRMLeadStatusUpdate.model_validate(
        {
            "new_status": "qualified",
            "reason": "接口测试写入阶段历史",
        }
    )
    assert crm_request.change_reason == "接口测试写入阶段历史"
