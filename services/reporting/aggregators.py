"""智能报告 V2 聚合器。

聚合器的职责只有一个：从数据库事实表中计算指标。

它不负责：

* 不负责调用 Dify；
* 不负责生成 HTML；
* 不负责写 report_generation 状态；
* 不负责做大段自然语言分析。

这样拆分的好处是：当面试官问“申请风险分从哪来”“ROI 有没有可能是 AI 编的”
时，可以明确回答：数字来自本文件的 SQL 和 ``rules.py``，AI 只做解释。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.reporting.registry import get_report_definition
from services.reporting.rules import (
    calculate_application_risk,
    calculate_channel_roi,
    calculate_conversion_rate,
    evaluate_complaint_sla,
)
from services.reporting.schemas import DataQuality, MetricTrace


@dataclass
class AggregatedReport:
    """聚合结果。

    ``content`` 是即将进入 Pydantic 报告 Schema 的内容；
    ``snapshot`` 是保存到 report_generation.aggregated_data_snapshot 的追溯快照；
    ``data_quality`` 说明空数据、可选数据源缺失、降级生成等情况。
    """

    content: dict[str, Any]
    snapshot: dict[str, Any]
    data_quality: DataQuality = field(default_factory=DataQuality)


def _default_period(period_start: Optional[date], period_end: Optional[date]) -> tuple[date, date]:
    """当调用方没有传周期时，默认统计最近 7 天。"""

    end = period_end or date.today()
    start = period_start or (end - timedelta(days=6))
    return start, end


def _date_params(start: date, end: date) -> dict[str, Any]:
    """统一 SQL 时间参数。

    MySQL DATETIME 查询使用 ``>= start_dt AND < end_next_dt``，避免结束日期当天
    23:59:59 的边界问题。
    """

    return {
        "start": start,
        "end": end,
        "start_dt": datetime.combine(start, datetime.min.time()),
        "end_next_dt": datetime.combine(end + timedelta(days=1), datetime.min.time()),
    }


def _rows(
    db: Session,
    sql: str,
    params: dict[str, Any],
    warnings: list[str],
    *,
    source_name: str,
    required: bool = False,
) -> list[Any]:
    """安全执行查询。

    对于 V2 新增事实表，正常初始化后应该存在；对于旧业务表，课程项目中可能还没建。
    因此默认把缺失表视为“可选数据源缺失”，记录数据质量警告后继续生成降级报告。
    如果某个报告的必需数据源缺失，可以把 ``required=True``，直接抛出异常。
    """

    try:
        return list(db.execute(text(sql), params).fetchall())
    except SQLAlchemyError as exc:
        message = f"{source_name} 数据源不可用：{exc.__class__.__name__}"
        if required:
            raise RuntimeError(message) from exc
        warnings.append(message)
        return []


def _scalar(
    db: Session,
    sql: str,
    params: dict[str, Any],
    warnings: list[str],
    *,
    source_name: str,
    default: Any = 0,
) -> Any:
    rows = _rows(db, sql, params, warnings, source_name=source_name)
    if not rows:
        return default
    return rows[0][0] if rows[0][0] is not None else default


def aggregate_report(
    db: Session,
    report_type: str,
    period_start: Optional[date],
    period_end: Optional[date],
    filters: Optional[dict[str, Any]] = None,
) -> AggregatedReport:
    """统一聚合入口。

    编排层只调用这个函数，不需要知道具体报告由哪个函数实现。
    """

    definition = get_report_definition(report_type)
    aggregator = globals()[definition.aggregator_name]
    start, end = _default_period(period_start, period_end)
    return aggregator(db, start, end, filters or {})


def aggregate_application_risk(
    db: Session,
    start: date,
    end: date,
    filters: dict[str, Any],
) -> AggregatedReport:
    """申请风险报告。

    业务价值：管理者不需要逐个打开学生申请，而是直接看到“哪些申请快逾期、
    哪些材料缺失、负责人是谁、下一步该做什么”。
    """

    warnings: list[str] = []
    params = _date_params(start, end)
    rows = _rows(
        db,
        """
        SELECT application_id, student_id, owner_id, material_name, required,
               deadline, submitted_time, status, update_time
        FROM application_material_item
        WHERE (deadline IS NULL OR deadline <= DATE_ADD(:end, INTERVAL 30 DAY))
        ORDER BY application_id, deadline
        """,
        params,
        warnings,
        source_name="application_material_item",
    )

    grouped: dict[int, list[Any]] = defaultdict(list)
    for row in rows:
        grouped[int(row[0])].append(row)

    today = end
    risk_items: list[dict[str, Any]] = []
    high = medium = low = overdue_count = missing_material_count = 0

    for application_id, items in grouped.items():
        student_id = items[0][1]
        owner_id = items[0][2]
        missing_materials: list[str] = []
        earliest_deadline: Optional[date] = None
        latest_update: Optional[datetime] = None

        for item in items:
            material_name = item[3]
            required = int(item[4] or 0)
            deadline = item[5]
            submitted_time = item[6]
            status = item[7]
            update_time = item[8]

            if deadline and (earliest_deadline is None or deadline < earliest_deadline):
                earliest_deadline = deadline
            if update_time and (latest_update is None or update_time > latest_update):
                latest_update = update_time
            if required and not submitted_time and status != "waived":
                missing_materials.append(material_name)

        overdue = bool(earliest_deadline and earliest_deadline < today and missing_materials)
        days_to_deadline = (earliest_deadline - today).days if earliest_deadline else None
        days_since_update = (today - latest_update.date()).days if latest_update else None

        risk = calculate_application_risk(
            overdue=overdue,
            days_to_deadline=days_to_deadline,
            missing_required_materials=len(missing_materials),
            days_since_update=days_since_update,
            has_next_action=False if missing_materials else True,
        )

        if risk.level == "high":
            high += 1
        elif risk.level == "medium":
            medium += 1
        else:
            low += 1
        if overdue:
            overdue_count += 1
        missing_material_count += len(missing_materials)

        if risk.score >= 40:
            risk_items.append(
                {
                    "application_id": application_id,
                    "student_id": student_id,
                    "owner_id": owner_id,
                    "stage": "material_preparation",
                    "risk_score": risk.score,
                    "risk_level": risk.level,
                    "risk_reasons": risk.reasons,
                    "missing_materials": missing_materials,
                    "next_action": "联系学生补齐必需材料并确认最近截止日期",
                }
            )

    metrics = {
        "total_applications": len(grouped),
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "overdue_count": overdue_count,
        "missing_material_count": missing_material_count,
    }
    content = {
        "summary": f"本周期共识别 {len(grouped)} 个申请，其中高风险 {high} 个。",
        "metrics": metrics,
        "risk_items": risk_items,
        "action_checklist": [
            {
                "owner_id": item["owner_id"],
                "action": f"处理申请 {item['application_id']} 的材料风险",
                "due_date": end.isoformat(),
                "priority": "high" if item["risk_level"] == "high" else "medium",
            }
            for item in risk_items
        ],
        "explanation": "风险分由规则引擎计算，AI 只负责解释和归纳。",
        "metric_traces": [
            MetricTrace(
                metric_name="application_risk_score",
                source_tables=["application_material_item"],
                formula="overdue + deadline + missing_materials + stale_update + no_next_action",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump()
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if not grouped:
        quality.level = "empty"
        quality.warnings.append("申请材料表在当前周期内没有可聚合数据")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_service_sla(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """服务 SLA 报告，覆盖投诉、行政申请和心理预警。"""

    warnings: list[str] = []
    params = _date_params(start, end)
    ticket_rows = _rows(
        db,
        """
        SELECT id, priority, create_time, first_response_time, resolved_time,
               status, satisfaction_score, owner_id
        FROM student_feedback_ticket
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        """,
        params,
        warnings,
        source_name="student_feedback_ticket",
    )

    complaint_sla: list[dict[str, Any]] = []
    response_overdue_count = 0
    resolve_overdue_count = 0
    response_hours_total = Decimal("0")
    response_hours_count = 0

    for row in ticket_rows:
        evaluation = evaluate_complaint_sla(
            priority=row[1],
            created_at=row[2],
            first_response_at=row[3],
            resolved_at=row[4],
        )
        if evaluation.response_overdue:
            response_overdue_count += 1
        if evaluation.resolve_overdue:
            resolve_overdue_count += 1
        if evaluation.response_hours is not None:
            response_hours_total += Decimal(str(evaluation.response_hours))
            response_hours_count += 1
        complaint_sla.append(
            {
                "ticket_id": row[0],
                "priority": row[1],
                "status": row[5],
                "owner_id": row[7],
                "response_hours": evaluation.response_hours,
                "resolve_hours": evaluation.resolve_hours,
                "response_overdue": evaluation.response_overdue,
                "resolve_overdue": evaluation.resolve_overdue,
                "thresholds": evaluation.thresholds,
            }
        )

    psych_rows = _rows(
        db,
        """
        SELECT id, student_id, risk_level, create_time, first_follow_time, status, owner_id
        FROM student_psych_alert
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        """,
        params,
        warnings,
        source_name="student_psych_alert",
    )
    psych_alert_sla: list[dict[str, Any]] = []
    psych_high_overdue = 0
    for row in psych_rows:
        first_follow_hours = None
        if row[4]:
            first_follow_hours = round((row[4] - row[3]).total_seconds() / 3600, 2)
        overdue = row[2] == "high" and (first_follow_hours is None or first_follow_hours > 1)
        if overdue:
            psych_high_overdue += 1
        psych_alert_sla.append(
            {
                "alert_id": row[0],
                "student_id": row[1],
                "risk_level": row[2],
                "status": row[5],
                "owner_id": row[6],
                "first_follow_hours": first_follow_hours,
                "high_risk_follow_overdue": overdue,
            }
        )

    total_services = len(ticket_rows) + len(psych_rows)
    avg_response = (
        float((response_hours_total / Decimal(response_hours_count)).quantize(Decimal("0.01")))
        if response_hours_count
        else None
    )
    content = {
        "summary": f"本周期共统计 {total_services} 条服务 SLA 记录。",
        "sla_overview": {
            "total_complaints": len(ticket_rows),
            "complaint_response_overdue_count": response_overdue_count,
            "complaint_resolve_overdue_count": resolve_overdue_count,
            "avg_first_response_hours": avg_response,
            "psych_alert_count": len(psych_rows),
            "psych_high_risk_follow_overdue_count": psych_high_overdue,
        },
        "complaint_sla": complaint_sla,
        "admin_service_sla": [],
        "psych_alert_sla": psych_alert_sla,
        "backlog_aging": [
            item for item in complaint_sla if item["status"] not in ("resolved", "closed")
        ],
        "explanation": "SLA 是否超时由固定阈值计算，心理预警不输出学生原文。",
        "metric_traces": [
            MetricTrace(
                metric_name="complaint_sla",
                source_tables=["student_feedback_ticket"],
                formula="first_response_time/resolved_time - create_time 与优先级阈值比较",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump(),
            MetricTrace(
                metric_name="psych_high_risk_follow_sla",
                source_tables=["student_psych_alert"],
                formula="高风险预警 first_follow_time - create_time <= 1小时",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump(),
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if total_services == 0:
        quality.level = "empty"
        quality.warnings.append("当前周期没有可统计的 SLA 数据")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_channel_roi(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """渠道 ROI 报告。"""

    warnings: list[str] = []
    params = _date_params(start, end)
    cost_rows = _rows(
        db,
        """
        SELECT channel, COALESCE(SUM(cost_amount), 0)
        FROM marketing_channel_cost
        WHERE cost_date >= :start AND cost_date <= :end
        GROUP BY channel
        """,
        params,
        warnings,
        source_name="marketing_channel_cost",
    )
    costs = {row[0]: Decimal(str(row[1] or 0)) for row in cost_rows}

    lead_rows = _rows(
        db,
        """
        SELECT source_channel, COUNT(*)
        FROM crm_lead
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        GROUP BY source_channel
        """,
        params,
        warnings,
        source_name="crm_lead",
    )
    leads = {row[0] or "unknown": int(row[1]) for row in lead_rows}

    contract_rows = _rows(
        db,
        """
        SELECT channel, COUNT(*), COALESCE(SUM(contract_amount), 0)
        FROM customer_contract
        WHERE signed_time >= :start_dt AND signed_time < :end_next_dt
          AND status = 'signed'
        GROUP BY channel
        """,
        params,
        warnings,
        source_name="customer_contract",
    )
    signed = {row[0] or "unknown": {"count": int(row[1]), "amount": Decimal(str(row[2] or 0))} for row in contract_rows}

    payment_rows = _rows(
        db,
        """
        SELECT c.channel, COALESCE(SUM(p.payment_amount), 0)
        FROM customer_payment p
        JOIN customer_contract c ON c.id = p.contract_id
        WHERE p.payment_time >= :start_dt AND p.payment_time < :end_next_dt
          AND p.status = 'paid'
        GROUP BY c.channel
        """,
        params,
        warnings,
        source_name="customer_payment",
    )
    paid = {row[0] or "unknown": Decimal(str(row[1] or 0)) for row in payment_rows}

    channels = sorted(set(costs) | set(leads) | set(signed) | set(paid))
    channel_metrics: list[dict[str, Any]] = []
    for channel in channels:
        signed_info = signed.get(channel, {"count": 0, "amount": Decimal("0")})
        roi = calculate_channel_roi(
            channel_cost=costs.get(channel, Decimal("0")),
            leads=leads.get(channel, 0),
            signed_count=signed_info["count"],
            paid_amount=paid.get(channel, Decimal("0")),
        )
        warnings.extend([f"{channel}: {warning}" for warning in roi.data_quality_warnings])
        channel_metrics.append(
            {
                "channel": channel,
                "cost": float(costs.get(channel, Decimal("0"))),
                "leads": leads.get(channel, 0),
                "valid_customer_rate": calculate_conversion_rate(signed_info["count"], leads.get(channel, 0)),
                "signed_count": signed_info["count"],
                "contract_amount": float(signed_info["amount"]),
                "paid_amount": float(paid.get(channel, Decimal("0"))),
                "cpl": roi.cpl,
                "cac": roi.cac,
                "roi": roi.roi,
            }
        )

    content = {
        "summary": f"本周期共统计 {len(channels)} 个渠道的成本、线索、签约和回款。",
        "channel_metrics": channel_metrics,
        "data_quality_warnings": warnings,
        "explanation": "CPL/CAC/ROI 均由成本、线索、合同、回款事实表计算。",
        "metric_traces": [
            MetricTrace(
                metric_name="channel_roi",
                source_tables=["marketing_channel_cost", "crm_lead", "customer_contract", "customer_payment"],
                formula="CPL=成本/线索数，CAC=成本/签约数，ROI=(回款-成本)/成本",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump()
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if not channels:
        quality.level = "empty"
        quality.warnings.append("当前周期没有渠道 ROI 可统计数据")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_sales_funnel(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """销售漏斗报告。"""

    warnings: list[str] = []
    params = _date_params(start, end)
    rows = _rows(
        db,
        """
        SELECT status, COUNT(*)
        FROM crm_lead
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        GROUP BY status
        """,
        params,
        warnings,
        source_name="crm_lead",
    )
    funnel_counts = {row[0] or "unknown": int(row[1]) for row in rows}
    total = sum(funnel_counts.values())
    signed = funnel_counts.get("signed", 0) + funnel_counts.get("contracted", 0)

    stalled_rows = _rows(
        db,
        """
        SELECT id, status, owner_employee_id, last_follow_time, create_time
        FROM crm_lead
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        """,
        params,
        warnings,
        source_name="crm_lead",
    )
    stalled_leads: list[dict[str, Any]] = []
    now_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())
    for row in stalled_rows:
        lead_id, status, owner_id, last_follow_time, create_time = row
        reference_time = last_follow_time or create_time
        days_idle = (now_dt - reference_time).days if reference_time else None
        risk_level = None
        if status == "new" and days_idle is not None and days_idle >= 1:
            risk_level = "high"
        elif status == "contacting" and days_idle is not None and days_idle >= 3:
            risk_level = "medium"
        elif status == "qualified" and days_idle is not None and days_idle >= 2:
            risk_level = "high"
        if risk_level:
            stalled_leads.append(
                {
                    "lead_id": lead_id,
                    "status": status,
                    "owner_id": owner_id,
                    "days_idle": days_idle,
                    "risk_level": risk_level,
                }
            )

    content = {
        "summary": f"本周期漏斗线索 {total} 条，签约 {signed} 条。",
        "funnel_counts": funnel_counts,
        "conversion_rates": {"signed_rate": calculate_conversion_rate(signed, total)},
        "avg_stage_stay_days": {},
        "stalled_leads": stalled_leads,
        "consultant_performance": [],
        "explanation": "转化率按同一创建周期客户 Cohort 计算，避免混合不同批次。",
        "metric_traces": [
            MetricTrace(
                metric_name="sales_funnel_conversion",
                source_tables=["crm_lead", "crm_lead_status_history"],
                formula="同一 create_time 周期内 signed_count / total_leads",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump()
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if total == 0:
        quality.level = "empty"
        quality.warnings.append("当前周期没有 CRM 线索数据")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_action_closure(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """行动闭环报告。"""

    warnings: list[str] = []
    params = _date_params(start, end)
    rows = _rows(
        db,
        """
        SELECT id, report_id, risk_code, owner_id, due_time, status,
               target_value, actual_value, completed_time, create_time
        FROM report_action
        WHERE create_time >= :start_dt AND create_time < :end_next_dt
        """,
        params,
        warnings,
        source_name="report_action",
    )
    total = len(rows)
    done = sum(1 for row in rows if row[5] == "done")
    on_time = sum(1 for row in rows if row[5] == "done" and row[8] and row[4] and row[8] <= row[4])
    overdue_actions = [
        {
            "action_id": row[0],
            "report_id": row[1],
            "risk_code": row[2],
            "owner_id": row[3],
            "due_time": row[4].isoformat() if row[4] else None,
            "status": row[5],
        }
        for row in rows
        if row[4] and row[5] != "done" and row[4] < datetime.combine(end + timedelta(days=1), datetime.min.time())
    ]
    repeated_codes = defaultdict(int)
    for row in rows:
        if row[2] and row[5] != "done":
            repeated_codes[row[2]] += 1

    content = {
        "summary": f"本周期共有 {total} 个报告行动项，已完成 {done} 个。",
        "metrics": {
            "action_count": total,
            "completion_rate": calculate_conversion_rate(done, total),
            "on_time_completion_rate": calculate_conversion_rate(on_time, total),
            "overdue_count": len(overdue_actions),
        },
        "overdue_actions": overdue_actions,
        "repeated_issues": [
            {"risk_code": code, "count": count}
            for code, count in repeated_codes.items()
            if count >= 2
        ],
        "target_achievement": [
            {
                "action_id": row[0],
                "target_value": float(row[6]) if row[6] is not None else None,
                "actual_value": float(row[7]) if row[7] is not None else None,
            }
            for row in rows
            if row[6] is not None or row[7] is not None
        ],
        "explanation": "AI 建议不会自动成为任务，必须进入 report_action 才参与闭环统计。",
        "metric_traces": [
            MetricTrace(
                metric_name="action_closure",
                source_tables=["report_action"],
                formula="完成率=done/total，按时完成率=按时done/total",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump()
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if total == 0:
        quality.level = "empty"
        quality.warnings.append("当前周期没有报告行动项")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_customer_ops(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """原有客户经营报告增强版。"""

    sales = aggregate_sales_funnel(db, start, end, filters)
    content = {
        "summary": sales.content["summary"],
        "metrics": {
            "total_leads": sum(sales.content.get("funnel_counts", {}).values()),
            "signed_rate": sales.content.get("conversion_rates", {}).get("signed_rate"),
        },
        "stage_distribution": [
            {"stage": stage, "count": count}
            for stage, count in sales.content.get("funnel_counts", {}).items()
        ],
        "stale_leads": sales.content.get("stalled_leads", []),
        "churn_analysis": [],
        "explanation": "客户经营报告复用销售漏斗 Cohort 指标，并补充长期未跟进风险。",
        "metric_traces": sales.content.get("metric_traces", []),
    }
    return AggregatedReport(content=content, snapshot=content, data_quality=sales.data_quality)


def aggregate_daily_summary(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """员工日报汇总。"""

    warnings: list[str] = []
    params = _date_params(start, end)
    total = _scalar(
        db,
        """
        SELECT COUNT(*)
        FROM employee_daily_report
        WHERE report_date >= :start AND report_date <= :end
        """,
        params,
        warnings,
        source_name="employee_daily_report",
    )
    content = {
        "summary": f"本周期共提交日报 {total} 份。",
        "metrics": {"submitted_count": int(total), "submission_rate": None},
        "key_progress": [],
        "common_risks": warnings.copy(),
        "next_plans": [],
        "explanation": "日报汇总用于发现团队进展、共性风险和下一步计划。",
        "metric_traces": [
            MetricTrace(
                metric_name="daily_report_submitted_count",
                source_tables=["employee_daily_report"],
                formula="COUNT(*)",
                filters={"period_start": start.isoformat(), "period_end": end.isoformat()},
            ).model_dump()
        ],
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    if not total:
        quality.level = "empty"
        quality.warnings.append("当前周期没有日报数据")
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)


def aggregate_psych_weekly(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """心理周报。注意：不读取、不输出学生心理原文。"""

    service = aggregate_service_sla(db, start, end, filters)
    overview = service.content.get("sla_overview", {})
    content = {
        "summary": f"本周期心理预警 {overview.get('psych_alert_count', 0)} 条。",
        "metrics": {
            "alert_count": overview.get("psych_alert_count", 0),
            "high_risk_follow_overdue_count": overview.get("psych_high_risk_follow_overdue_count", 0),
        },
        "emotion_trend": [],
        "alert_status": service.content.get("psych_alert_sla", []),
        "processing_timeliness": overview,
        "explanation": "心理报告只统计趋势、等级、状态和时效，禁止输出学生原文或诊断。",
        "metric_traces": service.content.get("metric_traces", []),
    }
    return AggregatedReport(content=content, snapshot=content, data_quality=service.data_quality)


def aggregate_complaint_weekly(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """投诉处理周报。"""

    service = aggregate_service_sla(db, start, end, filters)
    content = {
        "summary": f"本周期投诉工单 {service.content.get('sla_overview', {}).get('total_complaints', 0)} 条。",
        "metrics": service.content.get("sla_overview", {}),
        "sla_summary": service.content.get("sla_overview", {}),
        "high_frequency_issues": [],
        "explanation": "投诉周报重点看首次响应、解决时长、SLA 超时和满意度。",
        "metric_traces": service.content.get("metric_traces", []),
    }
    return AggregatedReport(content=content, snapshot=content, data_quality=service.data_quality)


def aggregate_weekly_summary(db: Session, start: date, end: date, filters: dict[str, Any]) -> AggregatedReport:
    """综合经营周报，跨 CRM、日报、心理、投诉。"""

    customer = aggregate_customer_ops(db, start, end, filters)
    daily = aggregate_daily_summary(db, start, end, filters)
    psych = aggregate_psych_weekly(db, start, end, filters)
    complaint = aggregate_complaint_weekly(db, start, end, filters)
    warnings = (
        customer.data_quality.warnings
        + daily.data_quality.warnings
        + psych.data_quality.warnings
        + complaint.data_quality.warnings
    )
    content = {
        "summary": "本周综合经营周报已汇总 CRM、日报、心理预警和投诉处理数据。",
        "business_sections": {
            "customer_ops": customer.content,
            "daily_summary": daily.content,
            "psych_weekly": psych.content,
            "complaint_weekly": complaint.content,
        },
        "cross_module_risks": warnings,
        "management_actions": [],
        "explanation": "综合周报用于管理层跨模块看趋势和风险，而不是替代单项明细报告。",
        "metric_traces": (
            customer.content.get("metric_traces", [])
            + daily.content.get("metric_traces", [])
            + psych.content.get("metric_traces", [])
            + complaint.content.get("metric_traces", [])
        ),
    }
    quality = DataQuality(level="warning" if warnings else "ok", warnings=warnings)
    return AggregatedReport(content=content, snapshot=content, data_quality=quality)

