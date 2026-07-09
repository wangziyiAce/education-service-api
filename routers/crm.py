"""
意向客户 & 跟进记录 - API 路由
接口清单：
  POST   /api/v1/crm/leads              新增意向客户
  GET    /api/v1/crm/leads              查询意向客户（支持条件搜索+分页）
  GET    /api/v1/crm/leads/{lead_id}    查询单个客户详情
  PUT    /api/v1/crm/leads/{lead_id}    更新客户信息
  PUT    /api/v1/crm/leads/{lead_id}/status   更新客户状态
  POST   /api/v1/crm/leads/{lead_id}/follow-ups   新增跟进记录
  GET    /api/v1/crm/leads/{lead_id}/follow-ups   查询跟进历史

员工日报 - API 路由
接口清单：
  POST /api/v1/employee/daily-reports          提交日报
  GET  /api/v1/employee/daily-reports          查询日报（支持筛选）
  GET  /api/v1/employee/daily-reports/summary  日报汇总（管理层用）
  GET  /api/v1/employee/daily-reports/{id}     日报详情

⚠️ 注意：/summary 必须定义在 /{report_id} 之前，
         否则 FastAPI 会把 "summary" 当作 {report_id} 来匹配，导致 422 错误。

"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from schemas.crm import (
    LeadCreate, LeadUpdate, LeadStatusUpdate, LeadResponse,
    LeadListResponse, FollowUpCreate, FollowUpResponse,
    DailyReportCreate, DailyReportResponse, DailyReportSummaryResponse,
)
from services.crm_service import (
    CrmService, EmployeeService,
    BizError, ParamError, NotFoundError, RefNotFoundError,
    StateError, ConflictError,
)
from utils.database import get_db

crm_router = APIRouter(prefix="/api/v1/crm", tags=["CRM 意向客户管理"])
employee_router = APIRouter(prefix="/api/v1/employee", tags=["员工日报管理"])

logger = logging.getLogger(__name__)


# ==================== FastAPI 异常处理器 ====================

@crm_router.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    """统一业务异常处理：BizError 及其所有子类"""
    logger.warning(
        "BizError: method=%s path=%s code=%d message=%s",
        request.method, request.url.path, exc.code, exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


# ==================== 统一响应工具 ====================

def success_response(data=None, message: str = "success", code: int = 0):
    """统一成功响应"""
    return {"code": code, "message": message, "data": data}


# ==================== 意向客户 CRUD ====================

@crm_router.post("/leads", status_code=201,
                  summary="新增意向客户")
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    """
    新增意向客户。

    **业务规则：**
    - customer_name 必填
    - 新客户默认状态 new
    - owner_employee_id 默认为当前登录用户（当前版本: 从请求体获取）
    - 插入前校验 owner_employee_id 对应的 sys_user 存在且 user_type='employee'
    """
    logger.info("POST /api/v1/crm/leads customer_name=%s owner=%s",
                data.customer_name, data.owner_employee_id)
    service = CrmService(db)
    lead = service.create_lead(data)
    return success_response(
        data=LeadResponse.model_validate(lead).model_dump(),
        message="创建成功",
    )


@crm_router.get("/leads", summary="查询意向客户（支持条件搜索+分页）")
def list_leads(
    status: Optional[str] = Query(None, description="按状态筛选: new/contacting/qualified/signed/lost"),
    owner_employee_id: Optional[int] = Query(None, description="按负责人筛选"),
    keyword: Optional[str] = Query(None, description="按姓名/联系方式模糊搜索"),
    create_time_start: Optional[date] = Query(None, description="创建时间起始"),
    create_time_end: Optional[date] = Query(None, description="创建时间截止"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    查询意向客户列表。

    **权限规则：**
    - 员工：只能看到 owner_employee_id = current_user.id 的客户
    - 经理：可查看本部门员工的客户
    - 管理员：可查看全部客户
    （当前版本暂未实现完整权限过滤，通过 owner_employee_id 参数自行筛选）

    **Dify 白名单：** 此接口在白名单中，Dify 可通过 Service Token 调用。
    """
    logger.info("GET /api/v1/crm/leads status=%s owner=%s keyword=%s page=%d",
                status, owner_employee_id, keyword, page)
    service = CrmService(db)
    result = service.list_leads(
        status=status,
        owner_employee_id=owner_employee_id,
        keyword=keyword,
        create_time_start=create_time_start,
        create_time_end=create_time_end,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result.model_dump())


@crm_router.get("/leads/{lead_id}", summary="查询单个客户详情")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    logger.info("GET /api/v1/crm/leads/%d", lead_id)
    service = CrmService(db)
    lead = service.get_lead(lead_id)
    if not lead:
        raise NotFoundError("客户不存在")
    return success_response(data=LeadResponse.model_validate(lead).model_dump())


@crm_router.put("/leads/{lead_id}", summary="更新客户信息")
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /api/v1/crm/leads/%d fields=%s",
                lead_id, list(data.model_fields_set))
    service = CrmService(db)
    lead = service.update_lead(lead_id, data)
    if not lead:
        raise NotFoundError("客户不存在")
    return success_response(data=LeadResponse.model_validate(lead).model_dump())


@crm_router.put("/leads/{lead_id}/status", summary="更新客户状态（含业务规则校验）")
def update_lead_status(lead_id: int, data: LeadStatusUpdate,
                       db: Session = Depends(get_db)):
    """
    更新客户状态。

    **状态机约束：**
    ```
    new → contacting → qualified → signed（终态）
      │       │           │
      └───────┴───────────┴──────────→ lost（终态，必须填 lost_reason）
    ```
    - signed 和 lost 为终态，不能回退
    - 变更为 lost 时 lost_reason 必填
    - 使用条件 UPDATE 防并发状态覆盖
    """
    logger.info("PUT /api/v1/crm/leads/%d/status new=%s", lead_id, data.status)
    service = CrmService(db)
    lead = service.update_lead_status(lead_id, data)
    return success_response(
        data=LeadResponse.model_validate(lead).model_dump(),
        message="状态更新成功",
    )


# ==================== 跟进记录 ====================

@crm_router.post("/leads/{lead_id}/follow-ups",
                  status_code=201,
                  summary="新增跟进记录")
def create_follow_up(lead_id: int, data: FollowUpCreate,
                     db: Session = Depends(get_db)):
    """
    新增跟进记录。

    **业务规则：**
    - lead_id 对应的 crm_lead 记录必须存在（应用层逻辑外键校验）
    - content 为必填
    - 同步更新 crm_lead.last_contact_time 和 update_time
    """
    logger.info("POST /api/v1/crm/leads/%d/follow-ups type=%s employee=%d",
                lead_id, data.follow_type, data.employee_id)
    service = CrmService(db)
    follow_up = service.create_follow_up(lead_id, data)
    return success_response(
        data=FollowUpResponse.model_validate(follow_up).model_dump(),
        message="跟进记录已保存",
    )


@crm_router.get("/leads/{lead_id}/follow-ups",
                 summary="查询跟进历史")
def list_follow_ups(lead_id: int, db: Session = Depends(get_db)):
    logger.info("GET /api/v1/crm/leads/%d/follow-ups", lead_id)
    service = CrmService(db)
    if not service.get_lead(lead_id):
        raise NotFoundError("客户不存在")
    follow_ups = service.list_follow_ups(lead_id)
    return success_response(
        data=[FollowUpResponse.model_validate(f).model_dump() for f in follow_ups]
    )


# ==================== 员工日报 ====================

@employee_router.post("/daily-reports", status_code=201,
                      summary="提交日报")
def create_daily_report(data: DailyReportCreate, db: Session = Depends(get_db)):
    """
    提交日报。

    **业务规则：**
    - 同一员工同一天只能有一份日报（uk_employee_date 唯一索引约束）
    - report_date 不能是未来日期
    - 支持 Dify 将口述内容结构化后通过 API 提交
    """
    logger.info("POST /api/v1/employee/daily-reports employee=%d date=%s",
                data.employee_id, data.report_date)
    service = EmployeeService(db)
    report = service.create_report(data)
    return success_response(
        data=DailyReportResponse.model_validate(report).model_dump(),
        message="日报提交成功",
    )


@employee_router.get("/daily-reports",
                      summary="查询日报（支持按员工、日期、部门筛选）")
def list_daily_reports(
    employee_id: Optional[int] = Query(None, description="员工ID"),
    department: Optional[str] = Query(None, description="部门"),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="截止日期"),
    db: Session = Depends(get_db),
):
    logger.info("GET /api/v1/employee/daily-reports employee=%d dept=%s",
                employee_id, department)
    service = EmployeeService(db)
    reports = service.list_reports(
        employee_id=employee_id,
        department=department,
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(
        data=[DailyReportResponse.model_validate(r).model_dump() for r in reports]
    )


# ⚠️ /summary 必须在 /{report_id} 之前定义！
@employee_router.get("/daily-reports/summary",
                      summary="日报汇总（管理层用）")
def daily_report_summary(
    report_date: date = Query(..., description="汇总日期"),
    department: Optional[str] = Query(None, description="按部门筛选"),
    db: Session = Depends(get_db),
):
    logger.info("GET /api/v1/employee/daily-reports/summary date=%s dept=%s",
                report_date, department)
    service = EmployeeService(db)
    result = service.get_summary(report_date=report_date, department=department)
    return success_response(data=result.model_dump())


@employee_router.get("/daily-reports/{report_id}",
                      summary="日报详情")
def get_daily_report(report_id: int, db: Session = Depends(get_db)):
    logger.info("GET /api/v1/employee/daily-reports/%d", report_id)
    service = EmployeeService(db)
    report = service.get_report(report_id)
    if not report:
        raise NotFoundError("日报不存在")
    return success_response(data=DailyReportResponse.model_validate(report).model_dump())