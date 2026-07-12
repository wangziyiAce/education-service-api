"""报告行动项独立接口。

路径满足计划中的：

* ``GET /api/v1/report-actions/{id}``
* ``PATCH /api/v1/report-actions/{id}``
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.report import ReportAction, ReportGeneration
from schemas.report import ReportActionResponse, ReportActionUpdate
from utils.auth import CurrentUser, get_current_user
from utils.database import get_db


router = APIRouter()


def _can_access_action(db: Session, action: ReportAction, user: CurrentUser) -> None:
    report = db.query(ReportGeneration).filter_by(id=action.report_id).first()
    if user.role_code in {"admin", "manager", "team_leader"}:
        return
    if report and report.generated_by == user.id:
        return
    if action.owner_id == user.id:
        return
    raise HTTPException(status_code=403, detail="无权访问该行动项")


@router.get("/{action_id}", response_model=ReportActionResponse)
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportAction:
    action = db.query(ReportAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="行动项不存在")
    _can_access_action(db, action, current_user)
    return action


@router.patch("/{action_id}", response_model=ReportActionResponse)
def patch_action(
    action_id: int,
    request: ReportActionUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportAction:
    action = db.query(ReportAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="行动项不存在")
    _can_access_action(db, action, current_user)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(action, field, value)
    db.commit()
    db.refresh(action)
    return action

