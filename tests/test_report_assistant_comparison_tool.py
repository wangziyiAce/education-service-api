"""只读指标对比工具的集成契约测试。"""

from datetime import date, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.report import ReportGeneration
from services.reporting.assistant.schemas import ComparisonPeriod
from services.reporting.assistant.tools import tool_compare_report_metrics
import pytest
from utils.database import Base


def test_completed_reports_are_compared_with_four_bound_evidence_items_each():
    """验证工具选择精确周期报告，并为原值与派生值建立不可交换的证据。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[ReportGeneration.__table__])
    db = sessionmaker(bind=engine)()
    user = SimpleNamespace(id=7, role_code="admin")
    periods = ComparisonPeriod(
        current_start=date(2026, 7, 1), current_end=date(2026, 7, 7),
        previous_start=date(2026, 6, 24), previous_end=date(2026, 6, 30),
        current_label="本周", previous_label="上周",
    )
    for report_id, start, end, value in (
        (1, periods.current_start, periods.current_end, 5),
        (2, periods.previous_start, periods.previous_end, 3),
    ):
        db.add(ReportGeneration(
            id=report_id, report_type="application_risk", report_title="测试",
            period_start=start, period_end=end, status="completed", schema_version=2,
            generated_by=7, report_content={"metrics": {"high_risk_count": value}},
            data_quality={"level": "ok", "warnings": [], "data_source": "database"},
            create_time=datetime(2026, 7, report_id), update_time=datetime(2026, 7, report_id),
        ))
    db.commit()

    result = tool_compare_report_metrics(
        report_type="application_risk", comparison_period=periods,
        metric_names=["high_risk_count"], current_user=user, db=db,
    )

    comparison = result.data["comparison"][0]
    assert (comparison["current_value"], comparison["previous_value"], comparison["delta"]) == (5, 3, 2)
    evidence = result.data["evidence"]
    assert len(evidence) == 4
    assert len({item["evidence_id"] for item in evidence}) == 4
    assert [(item["comparison_role"], item["source_report_id"]) for item in evidence[:2]] == [
        ("current", 1), ("previous", 2)
    ]
    assert all(item["evidence_id"].startswith("E") and item["evidence_id"][1:].isdigit() for item in evidence)


def test_incompatible_period_granularity_is_rejected_before_comparison():
    """两期天数口径不同不能仅因 Schema 相同就直接比较。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[ReportGeneration.__table__])
    db = sessionmaker(bind=engine)()
    period = ComparisonPeriod(
        current_start=date(2026, 7, 1), current_end=date(2026, 7, 7),
        previous_start=date(2026, 6, 20), previous_end=date(2026, 6, 30),
        current_label="本周", previous_label="上一周期",
    )
    for report_id, start, end in ((1, period.current_start, period.current_end), (2, period.previous_start, period.previous_end)):
        db.add(ReportGeneration(id=report_id, report_type="application_risk", report_title="测试",
            period_start=start, period_end=end, status="completed", schema_version=2, generated_by=7,
            report_content={"metrics": {"high_risk_count": 1}}, data_quality={"level": "ok"}))
    db.commit()
    with pytest.raises(ValueError, match="不兼容"):
        tool_compare_report_metrics(report_type="application_risk", comparison_period=period,
            metric_names=["high_risk_count"], current_user=SimpleNamespace(id=7, role_code="admin"), db=db)


def test_duplicate_dimension_rows_are_rejected():
    """同一期同一精确维度出现两行时不得由字典静默覆盖。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[ReportGeneration.__table__])
    db = sessionmaker(bind=engine)()
    period = ComparisonPeriod(current_start=date(2026, 7, 1), current_end=date(2026, 7, 7),
        previous_start=date(2026, 6, 24), previous_end=date(2026, 6, 30), current_label="本周", previous_label="上周")
    duplicate = {"channel_metrics": [{"channel": "search", "roi": 1}, {"channel": "search", "roi": 2}]}
    for report_id, start, end in ((1, period.current_start, period.current_end), (2, period.previous_start, period.previous_end)):
        db.add(ReportGeneration(id=report_id, report_type="channel_roi", report_title="测试", period_start=start,
            period_end=end, status="completed", schema_version=2, generated_by=7,
            report_content=duplicate, data_quality={"level": "ok"}))
    db.commit()
    with pytest.raises(ValueError, match="重复维度"):
        tool_compare_report_metrics(report_type="channel_roi", comparison_period=period,
            metric_names=["roi"], current_user=SimpleNamespace(id=7, role_code="admin"), db=db)
