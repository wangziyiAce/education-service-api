from datetime import datetime

from services.reporting.rules import (
    APPLICATION_RISK_LEVEL_HIGH,
    APPLICATION_RISK_LEVEL_LOW,
    APPLICATION_RISK_LEVEL_MEDIUM,
    calculate_application_risk,
    calculate_channel_roi,
    calculate_conversion_rate,
    evaluate_complaint_sla,
)


def test_application_risk_score_combines_deadline_material_and_followup_rules():
    risk = calculate_application_risk(
        overdue=True,
        days_to_deadline=3,
        missing_required_materials=3,
        days_since_update=8,
        has_next_action=False,
    )

    assert risk.score == 140
    assert risk.level == APPLICATION_RISK_LEVEL_HIGH
    assert "overdue" in risk.reasons
    assert "missing_required_materials" in risk.reasons


def test_application_risk_levels_match_plan_thresholds():
    assert calculate_application_risk(score_override=20).level == APPLICATION_RISK_LEVEL_LOW
    assert calculate_application_risk(score_override=40).level == APPLICATION_RISK_LEVEL_MEDIUM
    assert calculate_application_risk(score_override=70).level == APPLICATION_RISK_LEVEL_HIGH


def test_channel_roi_returns_null_metrics_when_cost_or_denominator_invalid():
    metrics = calculate_channel_roi(channel_cost=0, leads=0, signed_count=0, paid_amount=0)

    assert metrics.cpl is None
    assert metrics.cac is None
    assert metrics.roi is None
    assert metrics.data_quality_warnings


def test_channel_roi_uses_real_paid_amount_and_cost_without_estimation():
    metrics = calculate_channel_roi(
        channel_cost=1000,
        leads=20,
        signed_count=2,
        paid_amount=2500,
    )

    assert metrics.cpl == 50
    assert metrics.cac == 500
    assert metrics.roi == 1.5


def test_conversion_rate_is_none_when_denominator_is_zero():
    assert calculate_conversion_rate(10, 0) is None
    assert calculate_conversion_rate(25, 100) == 0.25


def test_complaint_sla_detects_urgent_response_and_resolution_timeout():
    created_at = datetime(2026, 7, 9, 9, 0, 0)
    first_response_at = datetime(2026, 7, 9, 11, 0, 0)
    resolved_at = datetime(2026, 7, 10, 12, 0, 0)

    result = evaluate_complaint_sla(
        priority="urgent",
        created_at=created_at,
        first_response_at=first_response_at,
        resolved_at=resolved_at,
    )

    assert result.response_hours == 2
    assert result.resolve_hours == 27
    assert result.response_overdue is True
    assert result.resolve_overdue is True
