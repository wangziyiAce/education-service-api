"""智能报告最小事实数据维护接口。

这些接口不是完整 CRM/教务系统，只提供报告 V2 所需的最小事实数据入口：

* 申请材料：支撑 application_risk；
* 渠道成本：支撑 channel_roi；
* 合同与回款：支撑 channel_roi；
* 后续可以继续扩展为独立业务模块。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.report import (
    ApplicationMaterialItem,
    CustomerContract,
    CustomerPayment,
    MarketingChannelCost,
)
from schemas.report import (
    ApplicationMaterialCreate,
    ChannelCostCreate,
    CustomerContractCreate,
    CustomerPaymentCreate,
)
from utils.auth import CurrentUser, ensure_management_user, get_current_user
from utils.database import get_db


router = APIRouter()


@router.post("/application-materials", status_code=status.HTTP_201_CREATED)
def create_application_material(
    request: ApplicationMaterialCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    ensure_management_user(current_user)
    item = ApplicationMaterialItem(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/application-materials")
def list_application_materials(
    application_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    ensure_management_user(current_user)
    query = db.query(ApplicationMaterialItem)
    if application_id is not None:
        query = query.filter(ApplicationMaterialItem.application_id == application_id)
    return [
        {
            "id": item.id,
            "application_id": item.application_id,
            "student_id": item.student_id,
            "owner_id": item.owner_id,
            "material_name": item.material_name,
            "required": item.required,
            "deadline": item.deadline,
            "submitted_time": item.submitted_time,
            "status": item.status,
        }
        for item in query.order_by(ApplicationMaterialItem.create_time.desc()).limit(100).all()
    ]


@router.post("/channel-costs", status_code=status.HTTP_201_CREATED)
def create_channel_cost(
    request: ChannelCostCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    ensure_management_user(current_user)
    item = MarketingChannelCost(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/channel-costs")
def list_channel_costs(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    ensure_management_user(current_user)
    return [
        {
            "id": item.id,
            "channel": item.channel,
            "cost_date": item.cost_date,
            "campaign": item.campaign,
            "cost_amount": item.cost_amount,
        }
        for item in db.query(MarketingChannelCost).order_by(MarketingChannelCost.cost_date.desc()).limit(100).all()
    ]


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
def create_contract(
    request: CustomerContractCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    ensure_management_user(current_user)
    contract = CustomerContract(**request.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return {"id": contract.id}


@router.get("/contracts")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    ensure_management_user(current_user)
    return [
        {
            "id": item.id,
            "customer_id": item.customer_id,
            "lead_id": item.lead_id,
            "channel": item.channel,
            "contract_amount": item.contract_amount,
            "signed_time": item.signed_time,
            "status": item.status,
        }
        for item in db.query(CustomerContract).order_by(CustomerContract.create_time.desc()).limit(100).all()
    ]


@router.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(
    request: CustomerPaymentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    ensure_management_user(current_user)
    contract = db.query(CustomerContract).filter_by(id=request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    payment = CustomerPayment(**request.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return {"id": payment.id}


@router.get("/payments")
def list_payments(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    ensure_management_user(current_user)
    return [
        {
            "id": item.id,
            "contract_id": item.contract_id,
            "payment_amount": item.payment_amount,
            "payment_time": item.payment_time,
            "status": item.status,
        }
        for item in db.query(CustomerPayment).order_by(CustomerPayment.create_time.desc()).limit(100).all()
    ]

