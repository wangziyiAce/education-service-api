"""报告定时计划 API。

这些接口只维护计划配置，真正的 APScheduler 进程会读取 ``report_schedule``
并调用 orchestrator 创建报告任务。这样 API 服务和调度进程可以独立部署。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from models.report import ReportSchedule
from schemas.report import ReportScheduleCreate, ReportScheduleResponse, ReportScheduleUpdate
from services.reporting.registry import get_report_definition
from utils.auth import CurrentUser, ensure_report_permission, get_current_user
from utils.database import get_db


router = APIRouter()


def _get_definition_or_400(report_type: str):
    try:
        return get_report_definition(report_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    request: ReportScheduleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportSchedule:
    definition = _get_definition_or_400(request.report_type)
    ensure_report_permission(current_user, definition.allowed_roles)
    schedule = ReportSchedule(
        report_type=request.report_type,
        cron_expression=request.cron_expression,
        enabled=request.enabled,
        timezone=request.timezone,
        period_rule=request.period_rule,
        title_template=request.title_template,
        filters=request.filters,
        recipients=request.recipients,
        created_by=current_user.id,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("", response_model=list[ReportScheduleResponse])
def list_schedules(
    enabled: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ReportSchedule]:
    if current_user.role_code == "student" or current_user.user_type == "student":
        raise HTTPException(status_code=403, detail="学生角色禁止访问报告计划")
    query = db.query(ReportSchedule)
    if enabled is not None:
        query = query.filter(ReportSchedule.enabled == enabled)
    return query.order_by(ReportSchedule.create_time.desc()).all()


@router.get("/{schedule_id}", response_model=ReportScheduleResponse)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportSchedule:
    schedule = db.query(ReportSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="报告计划不存在")
    definition = _get_definition_or_400(schedule.report_type)
    ensure_report_permission(current_user, definition.allowed_roles)
    return schedule


@router.patch("/{schedule_id}", response_model=ReportScheduleResponse)
def update_schedule(
    schedule_id: int,
    request: ReportScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportSchedule:
    schedule = db.query(ReportSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="报告计划不存在")
    definition = _get_definition_or_400(schedule.report_type)
    ensure_report_permission(current_user, definition.allowed_roles)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    schedule = db.query(ReportSchedule).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="报告计划不存在")
    definition = _get_definition_or_400(schedule.report_type)
    ensure_report_permission(current_user, definition.allowed_roles)
    db.delete(schedule)
    db.commit()
    return {"deleted": True}
