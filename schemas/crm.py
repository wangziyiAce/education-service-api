"""
意向客户 & 跟进记录 - Pydantic Schema
员工日报 - Pydantic Schema
"""
from __future__ import annotations

from typing import Any, Literal, Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


# ==================== 客户画像研判 ====================

class ProfileRuleCreate(BaseModel):
    """创建画像研判规则的请求体。

    管理端将产品线、匹配条件和 AI 提示词提交给客户研判模块；规则内容随后会
    作为 Dify 工作流的输入。``rule_content`` 保持 JSON 结构，便于不同产品线
    按需扩展条件而不修改数据库字段。
    """

    product_line: str = Field(..., min_length=1, max_length=64, description="规则适用的产品线")
    rule_name: str = Field(..., min_length=1, max_length=128, description="便于运营人员识别的规则名称")
    rule_content: dict[str, Any] = Field(..., description="学历、年龄、语言成绩等结构化匹配条件")
    match_prompt: Optional[str] = Field(default=None, description="调用 AI 时附带的系统提示词")
    priority: int = Field(default=0, description="数值越大，自动研判时越优先匹配")


class ProfileRuleUpdate(BaseModel):
    """局部更新画像规则的请求体。

    所有字段都可选，Service 层会通过 ``exclude_unset=True`` 只更新前端实际提交的
    字段；不这样处理会把未填写字段错误覆盖为默认值。
    """

    product_line: Optional[str] = Field(default=None, min_length=1, max_length=64)
    rule_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    rule_content: Optional[dict[str, Any]] = None
    match_prompt: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[int] = Field(default=None, ge=0, le=1, description="1 表示启用，0 表示停用")


class ProfileRuleResponse(BaseModel):
    """画像规则的响应结构，对应 ``profile_rule`` 表的一条可管理配置。"""

    id: int
    product_line: str
    rule_name: str
    rule_content: dict[str, Any]
    match_prompt: Optional[str] = None
    priority: int
    status: int
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class CustomerSourceResponse(BaseModel):
    """客户资料来源响应，用于上传后的追溯与待研判列表展示。"""

    id: int
    source_type: str
    raw_content: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    parse_status: str
    parse_result: Optional[dict[str, Any]] = None
    parse_error: Optional[str] = None
    operator_id: Optional[int] = None
    create_time: datetime

    model_config = {"from_attributes": True}


class CustomerProfileResponse(BaseModel):
    """AI 研判输出的客户画像响应，对应 ``customer_profile`` 表。"""

    id: int
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    source_id: Optional[int] = None
    background_info: Optional[dict[str, Any]] = None
    match_result: Optional[str] = None
    matched_product: Optional[str] = None
    match_score: Optional[float] = None
    match_reason: Optional[str] = None
    recommended_programs: Optional[Any] = None
    evaluator_id: Optional[int] = None
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class ProfileDetailResponse(BaseModel):
    """客户资料与最新研判结果的合并响应，供前端轮询异步任务状态。"""

    source_id: int
    source_type: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    parse_status: str
    parse_error: Optional[str] = None
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    background_info: Optional[dict[str, Any]] = None
    match_result: Optional[str] = None
    matched_product: Optional[str] = None
    match_score: Optional[float] = None
    match_reason: Optional[str] = None
    recommended_programs: Optional[Any] = None
    source_create_time: datetime
    profile_update_time: Optional[datetime] = None


class AnalyzeRequest(BaseModel):
    """手动触发研判时可选指定规则；不传时由 Service 按优先级选择启用规则。"""

    rule_id: Optional[int] = Field(default=None, gt=0, description="指定的画像规则 ID")


# ==================== 意向客户 ====================

class LeadCreate(BaseModel):
    """新增意向客户"""
    customer_name: str = Field(..., max_length=64, examples=["李四"])
    contact_info: Optional[str] = Field(None, max_length=128, examples=["139xxxx0002"])
    gender: Optional[str] = Field(None, max_length=10, examples=["M"])
    age: Optional[int] = Field(None, examples=[25])
    education_level: Optional[str] = Field(None, examples=["本科"])
    intended_country: Optional[str] = Field(None, examples=["英国,美国"])
    intended_major: Optional[str] = Field(None, examples=["计算机科学"])
    source_channel: Optional[str] = Field(None, examples=["线上"])
    background_info: Optional[str] = Field(None, examples=["对UCL计算机硕士感兴趣，GPA 3.5"])
    customer_profile_id: Optional[int] = Field(None, examples=[1])
    remark: Optional[str] = Field(None, examples=["高意向客户，需尽快跟进"])
    owner_employee_id: int = Field(..., examples=[2])


class LeadUpdate(BaseModel):
    """更新意向客户信息（部分更新：所有字段 Optional，只更新传了的字段）"""
    customer_name: Optional[str] = None
    # Optional + 默认 None = 可选字段，客户端可以不传
    contact_info: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    intended_country: Optional[str] = None
    intended_major: Optional[str] = None
    source_channel: Optional[str] = None
    background_info: Optional[str] = None
    customer_profile_id: Optional[int] = None
    remark: Optional[str] = None
    owner_employee_id: Optional[int] = None


class LeadStatusUpdate(BaseModel):
    """更新客户状态"""
    status: Literal["new", "contacting", "qualified", "signed", "lost"] = Field(
        ..., description="客户状态：new(新)/contacting(跟进中)/qualified(已确认)/signed(已签约)/lost(已流失)",
        examples=["contacting"])
    # Literal 类型：FastAPI 自动校验，传入非法值直接返回 422
    lost_reason: Optional[str] = Field(None, max_length=255, description="仅 lost 时填写",
                                       examples=["价格太高"])


class LeadResponse(BaseModel):
    """客户响应模型"""
    id: int
    customer_name: str
    contact_info: str
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    intended_country: Optional[str] = None
    intended_major: Optional[str] = None
    source_channel: Optional[str] = None
    background_info: Optional[str] = None
    remark: Optional[str] = None
    status: str
    lost_reason: Optional[str] = None
    owner_employee_id: Optional[int] = None
    customer_profile_id: Optional[int] = None
    owner_name: Optional[str] = None
    last_contact_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
    # from_attributes=True：允许 model_validate(ORM对象) 直接从 ORM 属性读取数据
    # Pydantic v2 替代了 v1 的 class Config: orm_mode = True


class LeadListResponse(BaseModel):
    """客户列表响应（含分页）"""
    items: List[LeadResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ==================== 跟进记录 ====================

class FollowUpCreate(BaseModel):
    """新增跟进记录"""
    employee_id: int = Field(..., examples=[2])
    follow_type: Literal["phone", "wechat", "meeting", "email", "other"] = Field(
        ..., description="跟进方式：phone/wechat/meeting/email/other",
        examples=["wechat"])
    # Literal 限制只能选这5种跟进方式，FastAPI 自动校验
    content: str = Field(..., examples=["客户确认意向，下周面谈"])
    next_plan: Optional[str] = Field(None, max_length=255, examples=["安排线下咨询"])


class FollowUpResponse(BaseModel):
    """跟进记录响应"""
    id: int
    lead_id: int
    employee_id: int
    follow_type: str
    content: str
    next_plan: Optional[str] = None
    create_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 员工日报 ====================

class DailyReportCreate(BaseModel):
    """提交日报"""
    employee_id: int = Field(..., examples=[2])
    report_date: date = Field(..., examples=["2025-03-20"])
    status: Literal["draft", "submitted"] = Field(
        "draft", description="日报状态：draft(草稿)/submitted(已提交)",
        examples=["draft"])
    raw_content: Optional[str] = Field(None, description="口述/输入原文",
                                       examples=["今天跟进了3个客户..."])
    # raw_content: 员工原始口述，content: Dify/AI 结构化后的版本
    content: str = Field(..., description="AI结构化后的文本")
    key_progress: Optional[List[str]] = Field(None, examples=[["签约1单", "新增2个意向"]])
    # key_progress 和 risks 是字符串数组，支持多条进展/风险
    risks: Optional[List[str]] = Field(None, examples=[["客户A可能流失"]])
    next_plan: Optional[str] = Field(None, examples=["明天跟进新客户"])


class DailyReportResponse(BaseModel):
    """日报响应"""
    id: int
    employee_id: int
    report_date: date
    status: str
    raw_content: Optional[str] = None
    content: str
    key_progress: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    next_plan: Optional[str] = None
    create_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmployeeSummaryItem(BaseModel):
    """单个员工的日报汇总"""
    employee_id: int
    key_progress: Optional[List[str]] = None
    risks: Optional[List[str]] = None


class DailyReportSummaryResponse(BaseModel):
    """日报汇总响应（管理层用）"""
    report_date: date
    total_submitted: int
    employees: List[EmployeeSummaryItem]
