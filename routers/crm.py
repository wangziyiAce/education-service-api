"""CRM 最小联动接口。

这里不重建完整 CRM，只补一个报告 V2 必需动作：
客户阶段更新时同步写入 ``crm_lead_status_history``，用于 sales_funnel 报告计算
阶段转化率和阶段停留时间。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.report import CRMLeadStatusHistory
from schemas.report import CRMLeadStatusUpdate
from utils.auth import CurrentUser, ensure_management_user, get_current_user
from utils.database import get_db


router = APIRouter()


@router.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    request: CRMLeadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """更新客户阶段并写入状态历史。

    如果项目当前还没有 ``crm_lead`` 表，历史表仍会记录变化，报告可以先基于
    ``crm_lead_status_history`` 演示阶段流转。
    """

    ensure_management_user(current_user)
    history = CRMLeadStatusHistory(
        lead_id=lead_id,
        old_status=request.old_status,
        new_status=request.new_status,
        operator_id=current_user.id,
        change_reason=request.change_reason,
    )
    db.add(history)
    update_lead_table = True
    try:
        db.execute(
            text("UPDATE crm_lead SET status=:status WHERE id=:lead_id"),
            {"status": request.new_status, "lead_id": lead_id},
        )
    except SQLAlchemyError:
        # 课程项目中 crm_lead 可能尚未落表；不影响历史记录写入。
        update_lead_table = False
    db.commit()
    db.refresh(history)
    return {
        "history_id": history.id,
        "lead_id": lead_id,
        "new_status": request.new_status,
        "crm_lead_updated": update_lead_table,
    }
