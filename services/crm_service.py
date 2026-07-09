"""
CRM 业务逻辑服务
负责：意向客户 CRUD、状态流转校验、跟进记录管理
员工日报业务逻辑服务
负责：日报提交、查询、汇总统计
"""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import or_, update, func

from models.crm import CrmLead, CrmFollowUp, EmployeeDailyReport
from schemas.crm import (
    LeadCreate, LeadUpdate, LeadStatusUpdate,
    LeadListResponse,
    FollowUpCreate,
    DailyReportCreate,
    DailyReportSummaryResponse, EmployeeSummaryItem, LeadResponse,
)

# SysUser 模型可能尚未创建，做容错导入
try:
    from models.user import SysUser
    HAS_SYS_USER = True
except ImportError:
    HAS_SYS_USER = False


# ==================== 业务异常类（对齐 API 规范 V1.2 第 3 章错误码） ====================

class BizError(Exception):
    """业务异常基类，router 层统一捕获并转为 HTTPException"""
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ParamError(BizError):
    """参数校验失败 40001"""
    def __init__(self, message: str):
        super().__init__(code=40001, message=message, status_code=400)


class NotFoundError(BizError):
    """资源不存在 40401"""
    def __init__(self, message: str):
        super().__init__(code=40401, message=message, status_code=404)


class RefNotFoundError(BizError):
    """关联实体不存在 40402"""
    def __init__(self, entity: str, id_value: int):
        super().__init__(
            code=40402,
            message=f"{entity}不存在: id={id_value}",
            status_code=404
        )


class StateError(BizError):
    """状态不允许操作 40902 / 42204"""
    def __init__(self, message: str, code: int = 40902):
        super().__init__(code=code, message=message, status_code=422)


class ConflictError(BizError):
    """业务冲突 40901"""
    def __init__(self, message: str):
        super().__init__(code=40901, message=message, status_code=409)


# 客户状态流转规则：signed 和 lost 是终态，不可回退
VALID_STATUS_TRANSITIONS = {
    "new": ["contacting", "lost"],
    "contacting": ["qualified", "lost"],
    "qualified": ["signed", "lost"],
    "signed": [],       # 终态
    "lost": [],          # 终态
}


class CrmService:
    """意向客户 & 跟进记录 业务逻辑"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 意向客户 CRUD ====================

    def create_lead(self, data: LeadCreate) -> CrmLead:
        """
        新增意向客户

        业务规则：
        - customer_name 必填
        - 新客户默认状态 new
        - owner_employee_id 默认为当前登录用户（当前版本: 从请求体获取）
        - 插入前校验 owner_employee_id 对应的 sys_user 存在且 user_type='employee'
        """
        owner_id = data.owner_employee_id

        # 逻辑外键校验：校验负责人存在且为员工
        if owner_id is not None and HAS_SYS_USER:
            owner = self.db.query(SysUser).filter(
                SysUser.id == owner_id,
                SysUser.user_type == 'employee',
                SysUser.status == 'normal'
            ).first()
            if not owner:
                raise RefNotFoundError("员工", owner_id)

        lead = CrmLead(
            status="new",
            **data.model_dump()
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def get_lead(self, lead_id: int) -> Optional[CrmLead]:
        """根据 ID 查询客户（排除已软删除的）"""
        return (
            self.db.query(CrmLead)
            .filter(CrmLead.id == lead_id, CrmLead.is_deleted == 0)
            .first()
        )

    def list_leads(
        self,
        status: Optional[str] = None,
        owner_employee_id: Optional[int] = None,
        keyword: Optional[str] = None,
        create_time_start: Optional[date] = None,
        create_time_end: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> LeadListResponse:
        """条件搜索 + 分页查询客户列表"""
        query = self.db.query(CrmLead).filter(CrmLead.is_deleted == 0)

        if status:
            query = query.filter(CrmLead.status == status)
        if owner_employee_id:
            query = query.filter(CrmLead.owner_employee_id == owner_employee_id)
        if keyword:
            query = query.filter(
                or_(
                    CrmLead.customer_name.contains(keyword),
                    CrmLead.contact_info.contains(keyword),
                )
            )
        if create_time_start:
            query = query.filter(
                func.date(CrmLead.create_time) >= create_time_start
            )
        if create_time_end:
            query = query.filter(
                func.date(CrmLead.create_time) <= create_time_end
            )

        total = query.count()
        items = (
            query.order_by(CrmLead.create_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return LeadListResponse(
            items=[LeadResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_lead(self, lead_id: int, data: LeadUpdate) -> Optional[CrmLead]:
        """更新客户基本信息"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # 如果更新了 owner_employee_id，校验新负责人存在
        if "owner_employee_id" in update_data and HAS_SYS_USER:
            new_owner_id = update_data["owner_employee_id"]
            if new_owner_id is not None:
                owner = self.db.query(SysUser).filter(
                    SysUser.id == new_owner_id,
                    SysUser.user_type == 'employee',
                    SysUser.status == 'normal'
                ).first()
                if not owner:
                    raise RefNotFoundError("员工", new_owner_id)

        for key, value in update_data.items():
            setattr(lead, key, value)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def update_lead_status(self, lead_id: int, data: LeadStatusUpdate) -> CrmLead:
        """
        更新客户状态（含业务规则校验 + 条件更新防并发）

        状态机：
        new → contacting → qualified → signed（终态）
          │       │           │
          └───────┴───────────┴──────────→ lost（终态，必须填 lost_reason）

        - signed 和 lost 是终态，不能再变更
        - lost 时必须填写 lost_reason
        - 使用条件 UPDATE 防并发状态覆盖
        """
        lead = self.get_lead(lead_id)
        if not lead:
            raise NotFoundError("客户不存在")

        current_status = lead.status
        new_status = data.status

        # 校验状态流转合法性
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise StateError(
                f"状态流转不合法：'{current_status}' → '{new_status}'。"
                f"允许的目标状态：{allowed if allowed else '无（当前为终态）'}",
                code=42204,
            )

        # lost 时必须填写原因
        if new_status == "lost" and not data.lost_reason:
            raise ParamError("客户状态变更为 lost 时，必须填写 lost_reason")

        # 条件更新防并发：只有当前状态匹配时才更新
        values = {
            "status": new_status,
            "update_time": func.now(),
        }
        if new_status == "lost" and data.lost_reason:
            values["lost_reason"] = data.lost_reason

        result = self.db.execute(
            update(CrmLead)
            .where(
                CrmLead.id == lead_id,
                CrmLead.status == current_status,  # 乐观锁条件
            )
            .values(**values)
        )

        if result.rowcount == 0:
            raise ConflictError("状态已被其他操作修改，请刷新后重试")

        self.db.commit()
        self.db.refresh(lead)
        return lead

    # ==================== 跟进记录 ====================

    def create_follow_up(self, lead_id: int, data: FollowUpCreate) -> CrmFollowUp:
        """
        新增跟进记录

        业务规则：
        - lead_id 对应的 crm_lead 记录必须存在（应用层逻辑外键校验）
        - content 为必填
        - 同步更新 crm_lead.last_contact_time 和 update_time（在同一事务中）
        """
        # 逻辑外键校验：客户必须存在
        lead = self.get_lead(lead_id)
        if not lead:
            raise NotFoundError(f"意向客户不存在: id={lead_id}")

        with self.db.begin():
            # 创建跟进记录
            follow_up = CrmFollowUp(lead_id=lead_id, **data.model_dump())
            self.db.add(follow_up)

            # 同步更新客户最后联系时间和更新时间
            self.db.execute(
                update(CrmLead)
                .where(CrmLead.id == lead_id)
                .values(
                    last_contact_time=func.now(),
                    update_time=func.now(),
                )
            )

        self.db.refresh(follow_up)
        return follow_up

    def list_follow_ups(self, lead_id: int) -> List[CrmFollowUp]:
        """查询某客户的跟进历史（按时间倒序，排除已删除）"""
        return (
            self.db.query(CrmFollowUp)
            .filter(
                CrmFollowUp.lead_id == lead_id,
                CrmFollowUp.is_deleted == 0,
            )
            .order_by(CrmFollowUp.create_time.desc())
            .all()
        )


class EmployeeService:
    """员工日报 业务逻辑"""

    def __init__(self, db: Session):
        self.db = db

    def create_report(self, data: DailyReportCreate) -> EmployeeDailyReport:
        """
        提交日报

        业务规则：
        - 同一员工同一天只能提交一条日报（唯一约束）
        - report_date 不能是未来日期
        - 校验 employee_id 对应的 sys_user 存在且 user_type='employee'
        """
        # 日期校验
        if data.report_date > date.today():
            raise ParamError("report_date 不能是未来日期")

        # 逻辑外键校验：员工存在
        if HAS_SYS_USER:
            employee = self.db.query(SysUser).filter(
                SysUser.id == data.employee_id,
                SysUser.user_type == 'employee',
            ).first()
            if not employee:
                raise RefNotFoundError("员工", data.employee_id)

        # 检查是否已存在同日日报
        existing = (
            self.db.query(EmployeeDailyReport)
            .filter(
                EmployeeDailyReport.employee_id == data.employee_id,
                EmployeeDailyReport.report_date == data.report_date,
            )
            .first()
        )
        if existing:
            raise ConflictError(
                f"员工 {data.employee_id} 在 {data.report_date} 已提交过日报，"
                "如需修改请使用更新接口"
            )

        report = EmployeeDailyReport(**data.model_dump())
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: int) -> Optional[EmployeeDailyReport]:
        return self.db.query(EmployeeDailyReport).filter(
            EmployeeDailyReport.id == report_id
        ).first()

    def list_reports(
        self,
        employee_id: Optional[int] = None,
        department: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[EmployeeDailyReport]:
        """条件查询日报列表"""
        query = self.db.query(EmployeeDailyReport)

        if employee_id:
            query = query.filter(EmployeeDailyReport.employee_id == employee_id)
        if department:
            query = query.filter(EmployeeDailyReport.department == department)
        if start_date:
            query = query.filter(EmployeeDailyReport.report_date >= start_date)
        if end_date:
            query = query.filter(EmployeeDailyReport.report_date <= end_date)

        return query.order_by(EmployeeDailyReport.report_date.desc()).all()

    def get_summary(
        self, report_date: date, department: Optional[str] = None
    ) -> DailyReportSummaryResponse:
        """
        日报汇总（管理层用）
        - 统计指定日期（+可选部门）的日报提交情况
        - 汇总每个员工的关键进展和风险
        """
        query = self.db.query(EmployeeDailyReport).filter(
            EmployeeDailyReport.report_date == report_date
        )
        if department:
            query = query.filter(EmployeeDailyReport.department == department)

        reports = query.all()

        employees = [
            EmployeeSummaryItem(
                employee_id=r.employee_id,
                employee_name=r.employee_name,
                key_progress=r.key_progress or [],
                risks=r.risks or [],
            )
            for r in reports
        ]

        return DailyReportSummaryResponse(
            report_date=report_date,
            department=department,
            total_submitted=len(reports),
            employees=employees,
        )