"""智能报告 V2 独立调度进程。

运行方式：

    python report_scheduler.py

为什么不用 FastAPI 进程直接跑定时任务？
--------------------------------------
在真实项目中，API 服务可能启动多个 worker。如果每个 worker 都启动调度器，
同一份周报可能被生成多次。独立 APScheduler 进程配合幂等键可以避免重复。

本调度器配置：

* timezone = Asia/Shanghai；
* coalesce = true：服务停顿期间错过多次触发时合并执行一次；
* max_instances = 1：同一任务不并发执行；
* 幂等键 = schedule_id + 统计周期。
"""

from __future__ import annotations

import logging

from models.report import ReportSchedule
from services.reporting.orchestrator import create_report_task, generate_report, resolve_period
from services.reporting.registry import get_report_definition
from utils.database import SessionLocal


logger = logging.getLogger(__name__)


def run_schedule_once(schedule_id: int) -> None:
    """执行单个定时计划。

    APScheduler 到点后只调用这个函数。真正的报告创建和生成仍走 orchestrator，
    保证手动、重试、定时三条入口行为一致。
    """

    db = SessionLocal()
    try:
        schedule = db.query(ReportSchedule).filter_by(id=schedule_id, enabled=1).first()
        if not schedule:
            return
        definition = get_report_definition(schedule.report_type)
        title_template = schedule.title_template or f"{definition.label} {{start}}~{{end}}"
        period_start, period_end = resolve_period(None, None, period_rule=schedule.period_rule)
        title = title_template.format(
            start=period_start.isoformat(),
            end=period_end.isoformat(),
            report_type=schedule.report_type,
        )
        report = create_report_task(
            db,
            report_type=schedule.report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            generated_by=schedule.created_by,
            request_filters=schedule.filters or {},
            trigger_source="schedule",
            schedule_id=schedule.id,
        )
        result = generate_report(report.id, db)
        schedule.last_status = result.status
        schedule.last_error = result.error_message
        schedule.last_run_time = result.completed_time
        db.commit()
    except Exception as exc:  # pragma: no cover - 需要真实数据库/调度环境
        logger.exception("报告计划执行失败 schedule_id=%s: %s", schedule_id, exc)
    finally:
        db.close()


def main() -> None:
    """启动 APScheduler 阻塞调度器。"""

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError as exc:  # pragma: no cover - 依赖安装提示
        raise SystemExit("请先安装 APScheduler：pip install apscheduler") from exc

    scheduler = BlockingScheduler(
        timezone="Asia/Shanghai",
        job_defaults={"coalesce": True, "max_instances": 1},
    )
    db = SessionLocal()
    try:
        schedules = db.query(ReportSchedule).filter_by(enabled=1).all()
        for schedule in schedules:
            scheduler.add_job(
                run_schedule_once,
                CronTrigger.from_crontab(schedule.cron_expression, timezone=schedule.timezone),
                args=[schedule.id],
                id=f"report_schedule_{schedule.id}",
                replace_existing=True,
            )
    finally:
        db.close()

    logger.info("智能报告调度器启动")
    scheduler.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
