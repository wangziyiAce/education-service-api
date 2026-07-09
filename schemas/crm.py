"""
客户研判模块 — Pydantic Schema
===========================================
客户画像研判相关的请求/响应数据结构。

包含:
  画像规则:
    ProfileRuleCreate    — 创建研判规则
    ProfileRuleUpdate    — 更新研判规则
    ProfileRuleResponse  — 规则详情响应

  客户来源:
    CustomerSourceResponse — 客户来源记录响应

  客户画像:
    CustomerProfileResponse — 画像研判结果响应
    AnalyzeRequest          — 触发 AI 研判请求

⭐ 字段命名严格对齐数据库列名（API 文档第 2.6 节）:
  - product_line（非 product）
  - rule_content（非 config / conditions）
  - match_prompt（非 prompt）
  - source_type（非 type）
  - parse_status（非 status）
  - parse_result（非 result）
  - match_result（非 result）
  - match_score（非 score）
  - match_reason（非 reason）
  - recommended_programs（非 recommendations）
  - background_info（非 background）
  - customer_name（非 name）
  - contact_info（非 phone + email）

参考文档:
  《教育服务系统_API接口设计规范文档_V1.2》
  - 第 9 章  客户研判模块接口
  - 第 2.6 节 字段命名与数据库对齐规范
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# 一、画像规则 Schema（profile_rule 表）
# ============================================================

class ProfileRuleCreate(BaseModel):
    """
    创建画像研判规则请求体。

    字段对齐 profile_rule 表。
    rule_content 是 JSON 对象，存储结构化的匹配条件（学历/语言/年龄等）。
    match_prompt 是发给 AI 的系统提示词。
    """

    product_line: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="产品线（留学申请/背景提升/硕博连读）",
        examples=["硕博连读"],
    )
    rule_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="规则名称，如'硕博连读-本科毕业生匹配规则'",
    )
    rule_content: Dict[str, Any] = Field(
        ...,
        description="研判规则配置（JSON 对象），示例: {conditions: {education: ['本科'], age_range: [22,35]}}",
    )
    match_prompt: Optional[str] = Field(
        default=None,
        description="AI 研判使用的系统提示词（可选，不填使用默认提示词）",
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="优先级（数值越大越优先匹配），默认 0",
    )


class ProfileRuleUpdate(BaseModel):
    """
    更新画像研判规则请求体。

    所有字段可选，只传需要修改的字段。
    """

    product_line: Optional[str] = Field(
        default=None,
        max_length=64,
        description="产品线",
    )
    rule_name: Optional[str] = Field(
        default=None,
        max_length=128,
        description="规则名称",
    )
    rule_content: Optional[Dict[str, Any]] = Field(
        default=None,
        description="研判规则配置（完整替换）",
    )
    match_prompt: Optional[str] = Field(
        default=None,
        description="AI 研判提示词",
    )
    priority: Optional[int] = Field(
        default=None,
        ge=0,
        description="优先级",
    )
    status: Optional[int] = Field(
        default=None,
        ge=0,
        le=1,
        description="状态: 1=启用 0=禁用",
    )


class ProfileRuleResponse(BaseModel):
    """
    画像规则响应体。

    字段严格对齐 profile_rule 表。
    """

    id: int = Field(..., description="主键")
    product_line: str = Field(..., description="产品线")
    rule_name: str = Field(..., description="规则名称")
    rule_content: Dict[str, Any] = Field(..., description="研判规则配置（JSON）")
    match_prompt: Optional[str] = Field(default=None, description="AI 研判提示词")
    priority: int = Field(..., description="优先级")
    status: int = Field(..., description="状态: 1=启用 0=禁用")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


# ============================================================
# 二、客户来源 Schema（customer_source 表）
# ============================================================

class CustomerSourceResponse(BaseModel):
    """
    客户来源记录响应体。

    字段严格对齐 customer_source 表。
    注意: 此表没有 update_time（设计如此，见数据库文档 6.3.2 节）。
    解析状态变更通过 parse_status 字段跟踪。

    parse_result 是 AI 解析后的结构化 JSON:
      {name: "张三", age: 24, education: "本科", ...}
    """

    id: int = Field(..., description="主键")
    source_type: str = Field(..., description="来源类型（text/pdf_resume/excel/import/manual）")
    raw_content: Optional[str] = Field(default=None, description="原始文本内容")
    file_url: Optional[str] = Field(default=None, description="上传文件 URL")
    file_name: Optional[str] = Field(default=None, description="原始文件名")
    parse_status: str = Field(..., description="解析状态（pending/success/failed）")
    parse_result: Optional[Dict[str, Any]] = Field(default=None, description="AI 解析后的结构化结果")
    parse_error: Optional[str] = Field(default=None, description="解析失败原因")
    operator_id: Optional[int] = Field(default=None, description="操作人ID（逻辑关联 sys_user）")
    create_time: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


# ============================================================
# 三、客户画像 Schema（customer_profile 表）
# ============================================================

class CustomerProfileResponse(BaseModel):
    """
    客户画像研判结果响应体。

    字段严格对齐 customer_profile 表（API 文档第 9.4 节）。

    match_result 枚举:
      matched     = 匹配成功，找到了合适的产品线
      partial     = 部分匹配，有条件不满足但有潜力
      not_matched = 未匹配，当前无适合产品线

    match_score: 0-100 的匹配度评分（DECIMAL(5,2)）
    recommended_programs: AI 推荐的具体项目列表（JSON 数组）
    """

    id: int = Field(..., description="主键")
    customer_name: Optional[str] = Field(default=None, description="客户姓名")
    contact_info: Optional[str] = Field(default=None, description="联系方式")
    source_id: Optional[int] = Field(default=None, description="→ customer_source.id（逻辑关联）")
    background_info: Optional[Dict[str, Any]] = Field(default=None, description="客户背景信息（JSON）")
    match_result: Optional[str] = Field(default=None, description="匹配结果（matched/partial/not_matched）")
    matched_product: Optional[str] = Field(default=None, description="匹配的产品线")
    match_score: Optional[Decimal] = Field(default=None, description="匹配度评分（0-100）")
    match_reason: Optional[str] = Field(default=None, description="AI 研判原因")
    recommended_programs: Optional[List[Dict[str, Any]]] = Field(default=None, description="推荐的专业/项目列表")
    evaluator_id: Optional[int] = Field(default=None, description="研判人ID（逻辑关联 sys_user）")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


# ============================================================
# 四、综合响应 Schema（上传+研判 联合查询）
# ============================================================

class ProfileDetailResponse(BaseModel):
    """
    客户研判完整详情（来源 + 画像联合查询结果）。

    对应 API 文档第 9.4 节 GET /api/v1/profile/{source_id} 的 data 字段。
    把 customer_source 和 customer_profile 的数据合并到一个响应中，
    前端一次请求即可获取完整信息。

    如果研判尚未完成（parse_status=pending），则 match_result 等字段为 null。
    """

    # --- 来源信息（来自 customer_source）---
    source_id: int = Field(..., description="来源记录ID")
    source_type: str = Field(..., description="来源类型")
    file_url: Optional[str] = Field(default=None, description="上传文件 URL")
    file_name: Optional[str] = Field(default=None, description="原始文件名")
    parse_status: str = Field(..., description="解析状态（pending/success/failed）")
    parse_error: Optional[str] = Field(default=None, description="解析失败原因")

    # --- 画像信息（来自 customer_profile，研判未完成时为 null）---
    customer_name: Optional[str] = Field(default=None, description="客户姓名")
    contact_info: Optional[str] = Field(default=None, description="联系方式")
    background_info: Optional[Dict[str, Any]] = Field(default=None, description="客户背景信息")
    match_result: Optional[str] = Field(default=None, description="匹配结果")
    matched_product: Optional[str] = Field(default=None, description="匹配的产品线")
    match_score: Optional[Decimal] = Field(default=None, description="匹配度评分")
    match_reason: Optional[str] = Field(default=None, description="AI 研判原因")
    recommended_programs: Optional[List[Dict[str, Any]]] = Field(default=None, description="推荐项目列表")

    # --- 时间 ---
    source_create_time: datetime = Field(..., description="资料上传时间")
    profile_update_time: Optional[datetime] = Field(default=None, description="研判完成时间")


class AnalyzeRequest(BaseModel):
    """
    触发 AI 研判请求体。

    对应 API 文档第 9.3 节 POST /api/v1/profile/{source_id}/analyze。
    当前版本不需要额外参数（source_id 从路径取，规则自动匹配）。
    预留此模型以便后续扩展（如指定某条规则、覆盖默认提示词）。
    """

    rule_id: Optional[int] = Field(
        default=None,
        description="指定使用的研判规则ID（可选，不填则自动按优先级匹配）",
    )
