"""
企业智能助手模块 - ORM 模型
包含: 意向客户、跟进记录、员工日报
"""
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Date, DateTime,
    JSON, Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from models.base import Base


class CrmLead(Base):
    """意向客户表"""
    __tablename__ = "crm_lead"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False, comment="客户姓名")
    contact_info = Column(String(50), nullable=False, comment="联系方式")
    gender = Column(String(10), comment="性别: M/F")
    age = Column(Integer, comment="年龄")
    education_level = Column(String(50), comment="学历层次")
    intended_country = Column(String(200), comment="意向国家")
    intended_major = Column(String(100), comment="意向专业")
    source_channel = Column(String(50), comment="来源渠道")
    background_info = Column(Text, comment="背景信息")
    remark = Column(Text, comment="备注")
    status = Column(String(20), nullable=False, default="new",
                    comment="状态: new/contacting/qualified/signed/lost")
    lost_reason = Column(String(255), comment="流失原因")
    owner_employee_id = Column(BigInteger, comment="负责员工ID")
    last_contact_time = Column(DateTime, comment="最后联系时间")
    is_deleted = Column(Integer, nullable=False, default=0,
                        comment="软删除标记: 0=正常 1=已删除")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 一对多关系：一个客户对应多条跟进记录
    follow_ups = relationship("CrmFollowUp", back_populates="lead", lazy="dynamic")

    __table_args__ = (
        Index("idx_crm_lead_status", "status"),
        Index("idx_crm_lead_owner", "owner_employee_id"),
        Index("idx_crm_lead_name", "customer_name"),
        Index("idx_crm_lead_last_contact", "last_contact_time"),
        Index("idx_crm_lead_is_deleted", "is_deleted"),
        Index("idx_crm_lead_create_time", "create_time"),
    )


class CrmFollowUp(Base):
    """客户跟进记录表"""
    __tablename__ = "crm_follow_up"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(BigInteger, nullable=False, comment="客户ID（逻辑关联 crm_lead.id）")
    employee_id = Column(BigInteger, nullable=False, comment="跟进员工ID")
    follow_type = Column(String(20), nullable=False,
                         comment="跟进方式: phone/wechat/meeting/email/other")
    content = Column(Text, nullable=False, comment="跟进内容")
    next_plan = Column(String(500), comment="下一步计划")
    is_deleted = Column(Integer, nullable=False, default=0,
                        comment="软删除标记: 0=正常 1=已删除")
    create_time = Column(DateTime, server_default=func.now())

    lead = relationship("CrmLead", back_populates="follow_ups")

    __table_args__ = (
        Index("idx_follow_up_lead", "lead_id"),
        Index("idx_follow_up_employee", "employee_id"),
    )


class EmployeeDailyReport(Base):
    """员工日报表"""
    __tablename__ = "employee_daily_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, nullable=False, comment="员工ID")
    employee_name = Column(String(50), comment="员工姓名")
    department = Column(String(50), comment="所属部门")
    report_date = Column(Date, nullable=False, comment="日报日期")
    raw_content = Column(Text, comment="口述/原文内容")
    content = Column(Text, comment="AI结构化后的内容")
    key_progress = Column(JSON, comment="关键进展数组")
    risks = Column(JSON, comment="风险项数组")
    next_plan = Column(Text, comment="明日计划")
    create_time = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_daily_report_employee", "employee_id"),
        Index("idx_daily_report_date", "report_date"),
        Index("idx_daily_report_dept", "department"),
        UniqueConstraint("employee_id", "report_date", name="uk_employee_date"),
    )