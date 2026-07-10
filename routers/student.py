"""学生服务最小联动接口。

本轮只补智能报告 V2 需要的投诉处理字段：
``first_response_time``、``resolved_time``、``satisfaction_score``。
这些字段会被 service_sla 和 complaint_weekly 报告使用。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.report import StudentFeedbackTicket
from schemas.report import FeedbackTicketUpdate
from utils.auth import CurrentUser, ensure_management_user, get_current_user
from utils.database import get_db


router = APIRouter()


@router.patch("/feedback-tickets/{ticket_id}")
def update_feedback_ticket(
    ticket_id: int,
    request: FeedbackTicketUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """处理投诉工单并同步响应/解决时间。"""

    ensure_management_user(current_user)
    ticket = db.query(StudentFeedbackTicket).filter_by(id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="投诉工单不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    # 如果状态被更新为处理中但未传首次响应时间，自动补当前时间，保证 SLA 可算。
    if request.status in {"processing", "resolved", "closed"} and ticket.first_response_time is None:
        ticket.first_response_time = datetime.now()
    if request.status in {"resolved", "closed"} and ticket.resolved_time is None:
        ticket.resolved_time = datetime.now()

    db.commit()
    db.refresh(ticket)
    return {
        "id": ticket.id,
        "status": ticket.status,
        "first_response_time": ticket.first_response_time,
        "resolved_time": ticket.resolved_time,
    }
