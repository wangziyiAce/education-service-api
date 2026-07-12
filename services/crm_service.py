"""
CRM 业务逻辑服务
负责：意向客户 CRUD、状态流转校验、跟进记录管理
员工日报业务逻辑服务
负责：日报提交、查询、汇总统计
"""
import json
import logging
import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_, update, func, text

from config import LLM_API_KEY, LLM_API_URL, LLM_MODEL, LLM_TIMEOUT
from models.crm import (
    CrmLead, CrmFollowUp, EmployeeDailyReport,
    AssistantMessage, AssistantSession,
)
from schemas.crm import (
    LeadCreate, LeadUpdate, LeadStatusUpdate,
    LeadListResponse,
    FollowUpCreate,
    DailyReportCreate,
    DailyReportManagementSummary,
    EmployeeSummaryItem, LeadResponse,
    AssistantChatRequest, AssistantChatResponse,
    AssistantMessageResponse, AssistantSessionResponse,
)

logger = logging.getLogger(__name__)

# SysUser 模型可能尚未创建，做容错导入
try:
    from models.user import SysUser
    HAS_SYS_USER = True
except ImportError:
    HAS_SYS_USER = False


# ==================== 业务异常类（对齐 API 规范 V1.2 第 3 章错误码） ====================

class BizError(Exception):
    """业务异常基类，router 层统一捕获并转为 JSON 错误响应"""
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        # 业务错误码，如 40001、40401，前端可根据此码做不同处理
        self.message = message
        # HTTP 状态码，由 exception_handler 读取并设置到响应上
        self.status_code = status_code
        super().__init__(message)
        # 调用 Exception.__init__，保留标准异常的堆栈跟踪能力


class ParamError(BizError):
    """参数校验失败 40001"""
    def __init__(self, message: str):
        super().__init__(code=40001, message=message, status_code=400)
        # 40001 = 请求参数不合法，前端可直接展示 message 给用户


class NotFoundError(BizError):
    """资源不存在 40401"""
    def __init__(self, message: str):
        super().__init__(code=40401, message=message, status_code=404)
        # 40401 = 请求的资源（客户/日报/跟进记录）不存在


class RefNotFoundError(BizError):
    """关联实体不存在 40402"""
    def __init__(self, entity: str, id_value: int):
        super().__init__(
            code=40402,
            message=f"{entity}不存在: id={id_value}",
            status_code=404
        )
        # 40402 = 逻辑外键校验失败，如 owner_employee_id 对应的员工不存在


class StateError(BizError):
    """状态不允许操作 40902 / 42204"""
    def __init__(self, message: str, code: int = 40902):
        super().__init__(code=code, message=message, status_code=422)
        # 42204 = 状态流转不合法（如从终态 signed 回退）


class ConflictError(BizError):
    """业务冲突 40901"""
    def __init__(self, message: str):
        super().__init__(code=40901, message=message, status_code=409)
        # 40901 = 并发冲突或重复提交（如同一员工同日重复提交日报）


# 客户状态流转规则：signed 和 lost 是终态，不可回退
VALID_STATUS_TRANSITIONS = {
    "new": ["contacting", "lost"],
    "contacting": ["qualified", "lost"],
    "qualified": ["signed", "lost"],
    "signed": [],       # 终态：已签约，不允许任何状态变更
    "lost": [],          # 终态：已流失，不允许任何状态变更
}
# 用途：update_lead_status() 中校验状态流转合法性
# 扩展：新增状态时只需在此字典中添加对应的允许目标状态列表


# ==================== LLM 辅助（共享工具，原 assistant_service 下沉） ====================

def _call_llm(system_prompt: str, user_content: str) -> Optional[str]:
    """调用 LLM Chat Completions API（同步阻塞）；未配置/失败返回 None。"""
    if not LLM_API_KEY:
        logger.warning("LLM_API_KEY 未配置，跳过 LLM 调用")
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("openai 包未安装，请执行: pip install openai>=1.30.0")
        return None
    try:
        import httpx
        # trust_env=False: 避免继承 Windows 系统代理导致 HTTPS TLS 握手失败
        _http_client = httpx.Client(timeout=LLM_TIMEOUT, trust_env=False)
        client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_API_URL,
            timeout=LLM_TIMEOUT,
            http_client=_http_client,
        )
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        logger.info(f"LLM 调用成功: model={LLM_MODEL}")
        return content
    except Exception as e:
        logger.error(f"LLM 调用失败: {type(e).__name__}: {e}")
        return None


def _extract_json(text: str) -> Optional[dict]:
    """从 LLM 返回文本中提取 JSON 对象（兼容 markdown 包裹/尾逗号）。"""
    if not text or not text.strip():
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.replace("```", "")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        fixed = re.sub(r",\s*}", "}", json_str)
        fixed = re.sub(r",\s*]", "]", fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    logger.warning("无法从 LLM 输出中提取 JSON")
    return None


def is_llm_available() -> bool:
    """检查 LLM 服务是否可用（仅检查配置，不发起网络请求）。"""
    if not LLM_API_KEY:
        return False
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        return False


def _crm_llm_text(system_prompt: str, user_content: str) -> Optional[str]:
    """调用大模型返回纯文本；未配置/失败返回 None（优雅降级，不抛错打断主流程）"""
    try:
        return _call_llm(system_prompt, user_content)
    except Exception:
        return None


def _crm_llm_json(system_prompt: str, user_content: str) -> Optional[dict]:
    """调用大模型并解析 JSON；失败/格式错误返回 None"""
    raw = _crm_llm_text(system_prompt, user_content)
    if not raw:
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


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
            # 三个条件：ID存在 + 用户类型为员工 + 账号正常，任一不满足则拒绝
        if not owner:
            raise RefNotFoundError("员工", owner_id)

        # LLM 结构化提取（替代外部 Dify）：用 raw_content 回填未提供的字段
        if getattr(data, "raw_content", None):
            extracted = self._llm_extract_lead_fields(data.raw_content)
            if extracted:
                for f in ["gender", "age", "education_level", "intended_country",
                          "intended_major", "source_channel", "contact_info",
                          "background_info", "remark"]:
                    if not getattr(data, f, None) and extracted.get(f):
                        setattr(data, f, extracted.get(f))

        lead = CrmLead(
            status="new",
            **data.model_dump(exclude={"raw_content"})
            # **data.model_dump(mode="json") 展开所有 Pydantic 字段为关键字参数
            # 排除 raw_content：该字段仅用于 LLM 抽取，不是 crm_lead 表的列
        )
        self.db.add(lead)
        # 将新对象加入 SQLAlchemy 会话的待插入队列
        self.db.commit()
        # 提交事务，生成 INSERT SQL 并执行，此时 lead.id 被数据库自动赋值
        self.db.refresh(lead)
        # 刷新对象，从数据库重新加载（获取自增 ID、server_default 默认值等）
        return lead

    def _llm_extract_lead_fields(self, raw: str) -> Optional[dict]:
        """调用大模型从自然语言描述中抽取客户结构化字段（失败返回 None）"""
        system = (
            "你是留学咨询公司的客户信息抽取助手。从用户自然语言描述中抽取客户结构化字段。\n"
            "只返回 JSON（不要其他内容）：\n"
            "{\"customer_name\":\"姓名或空\",\"gender\":\"男/女/空\",\"age\":数字或空,"
            "\"education_level\":\"学历或空\",\"intended_country\":\"意向国家或空\","
            "\"intended_major\":\"意向专业或空\",\"source_channel\":\"来源渠道或空\","
            "\"contact_info\":\"联系方式或空\",\"background_info\":\"背景补充或空\","
            "\"remark\":\"备注或空\"}\n"
            "规则：只抽取文本中明确提到的信息，未提及的字段留空；不要编造。"
        )
        return _crm_llm_json(system, raw)

    def generate_lead_insight(self, lead_id: int) -> Optional[str]:
        """基于客户资料+跟进历史，调用 LLM 生成客户洞察与下一步建议"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        follow_ups = self.list_follow_ups(lead_id)
        ctx = (
            f"客户姓名：{lead.customer_name}\n"
            f"状态：{lead.status}\n"
            f"意向国家：{lead.intended_country or '未知'}\n"
            f"意向专业：{lead.intended_major or '未知'}\n"
            f"学历：{lead.education_level or '未知'}\n"
            f"背景：{lead.background_info or '无'}\n"
            f"备注：{lead.remark or '无'}\n"
            f"跟进记录数：{len(follow_ups)}\n"
        )
        for fu in follow_ups[:10]:
            ctx += f"- [{fu.follow_type}] {fu.content}（下一步：{fu.next_plan or '无'}）\n"
        system = (
            "你是资深留学顾问。基于以下客户资料与跟进记录，生成一段简洁的客户洞察"
            "（当前阶段判断 + 核心诉求 + 下一步跟进建议）。150字以内，分点、专业、可落地。"
        )
        return _crm_llm_text(system, ctx)

    def summarize_leads(self, result: "LeadListResponse") -> Optional[str]:
        """对意向客户列表生成 LLM 摘要（可选 ai_summary 用）"""
        if not result or not result.items:
            return None
        lines = [
            f"- {it.customer_name}（{it.status}）："
            f"{it.intended_major or '未知专业'}，意向{it.intended_country or '未知'}"
            for it in result.items[:20]
        ]
        system = "你是销售主管助理。用 3-5 句话总结以下意向客户列表的整体情况（数量、阶段分布、重点机会）。"
        return _crm_llm_text(system, "\n".join(lines))

    def get_lead(self, lead_id: int) -> Optional[CrmLead]:
        """根据 ID 查询客户（排除已软删除的）"""
        return (
            self.db.query(CrmLead)
            .filter(CrmLead.id == lead_id)
            .first()
            # .first() 返回第一条匹配记录，无匹配则返回 None
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
        query = self.db.query(CrmLead)
        # 基础查询：意向客户列表

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
                # or_() = SQL 的 OR，姓名或联系方式任一匹配即返回
            )
        if create_time_start:
            query = query.filter(
                func.date(CrmLead.create_time) >= create_time_start
                # func.date() 提取 DATETIME 的日期部分，忽略时分秒
            )
        if create_time_end:
            query = query.filter(
                func.date(CrmLead.create_time) <= create_time_end
            )

        total = query.count()
        # 先 count 再分页：获取符合条件的总记录数（用于前端分页组件）
        items = (
            query.order_by(CrmLead.create_time.desc())
            .offset((page - 1) * page_size)
            # offset 跳过前 N 页的记录，page=1 时 offset=0
            .limit(page_size)
            # limit 限制每页条数
            .all()
        )

        return LeadListResponse(
            items=[LeadResponse.model_validate(item) for item in items],
            # model_validate：将 ORM 对象转为 Pydantic Schema，自动过滤未定义字段
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
        # exclude_unset=True：只导出客户端实际传了的字段，未传的字段不出现在 dict 中
        # 这样实现了"部分更新"：只修改传了的字段，未传的保持原值

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
            # 动态设置 ORM 对象属性，只修改 update_data 中有的字段

        # 若更新了 background_info，调用 LLM 重新抽取结构化标签回填空字段
        if update_data.get("background_info"):
            extracted = self._llm_extract_lead_fields(update_data["background_info"])
            if extracted:
                for f in ["gender", "age", "education_level", "intended_country",
                          "intended_major", "source_channel", "contact_info", "remark"]:
                    cur = getattr(lead, f, None)
                    if (cur is None or cur == "") and extracted.get(f):
                        setattr(lead, f, extracted.get(f))

        self.db.commit()
        # SQLAlchemy 自动追踪变更，只生成被修改字段的 UPDATE SET
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
        # 从 VALID_STATUS_TRANSITIONS 字典查询当前状态允许跳转到哪些状态

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
            # 条件 UPDATE：WHERE id=X AND status=current_status
            # 如果并发请求先改了状态，此处的 rowcount 将为 0
            .values(**values)
        )

        if result.rowcount == 0:
            raise ConflictError("状态已被其他操作修改，请刷新后重试")
        # rowcount=0 表示没有行被更新，说明 status 已被并发请求修改

        self.db.commit()
        self.db.refresh(lead)
        return lead

    def generate_status_suggestion(self, lead: "CrmLead", new_status: str) -> Optional[str]:
        """状态流转后调用 LLM 生成跟进/挽回建议"""
        ctx = (f"客户：{lead.customer_name}，状态刚变更为：{new_status}。"
               f"意向专业：{lead.intended_major or '未知'}，"
               f"意向国家：{lead.intended_country or '未知'}。")
        if new_status == "lost":
            system = "客户刚流失。给出 2-3 条流失挽回建议，简洁可执行，80字以内。"
        elif new_status == "signed":
            system = "客户刚签约。给出 2-3 条签约后跟进建议（如服务启动、转介绍），简洁可执行，80字以内。"
        else:
            system = "客户状态刚变更。给出 1-2 条下一步跟进建议，简洁可执行，60字以内。"
        return _crm_llm_text(system, ctx)

    # ==================== 跟进记录 ====================

    def create_follow_up(self, lead_id: int, data: FollowUpCreate) -> tuple[CrmFollowUp, Optional[str]]:
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

        # LLM 结构化（替代外部 Dify）：优先用 raw_content 生成 content / 建议 next_plan
        ai_next_plan = None
        if not data.content and data.raw_content:
            structured = self._llm_structure_follow_up(data.raw_content)
            if structured:
                data.content = structured.get("content") or data.raw_content
                ai_next_plan = structured.get("next_plan")
                if not data.next_plan and ai_next_plan:
                    data.next_plan = ai_next_plan
            else:
                data.content = data.raw_content
        if not data.content:
            raise ParamError("content 与 raw_content 至少提供一个")

        # 创建跟进记录
        follow_up = CrmFollowUp(lead_id=lead_id, **data.model_dump(exclude={"raw_content"}))
        # 排除 raw_content：该字段仅用于 LLM 抽取，不是 crm_follow_up 表的列
        self.db.add(follow_up)

        # 同步更新客户最后联系时间和更新时间（与跟进记录在同一事务中）
        self.db.execute(
            update(CrmLead)
            .where(CrmLead.id == lead_id)
            .values(
                last_contact_time=func.now(),
                update_time=func.now(),
            )
        )
        self.db.commit()

        self.db.refresh(follow_up)
        return follow_up, ai_next_plan

    def list_follow_ups(self, lead_id: int) -> List[CrmFollowUp]:
        """查询某客户的跟进历史（按时间倒序，排除已删除）"""
        return (
            self.db.query(CrmFollowUp)
            .filter(
                CrmFollowUp.lead_id == lead_id,
            )
            .order_by(CrmFollowUp.create_time.desc())
            .all()
        )

    def _llm_structure_follow_up(self, raw: str) -> Optional[dict]:
        """调用大模型将口述跟进整理为结构化 JSON"""
        system = (
            "你是销售跟进记录整理助手。将口述的跟进内容整理为结构化 JSON：\n"
            "{\"content\":\"整理后的跟进内容（简洁书面语）\","
            "\"next_plan\":\"下一步计划或空\"}\n只返回 JSON。"
        )
        return _crm_llm_json(system, raw)

    def summarize_follow_ups(self, lead_id: int) -> Optional[str]:
        """对某客户的跟进历史生成 LLM 摘要（可选 ai_summary 用）"""
        items = self.list_follow_ups(lead_id)
        if not items:
            return None
        lines = [
            f"- {fu.content}（方式：{fu.follow_type}，下一步：{fu.next_plan or '无'}）"
            for fu in items[:20]
        ]
        system = "你是销售助理。用 2-3 句话总结该客户的跟进历史与当前进展，80字以内。"
        return _crm_llm_text(system, "\n".join(lines))


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
        # 防止提交未来日期的日报，保证数据真实性

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
        # 应用层检查：同一员工同一天只能有一份日报
        # 数据库层也有 uk_employee_date 唯一索引做兜底保护

        # LLM 结构化提取（替代外部 Dify）：将口述原文拆为结构化日报字段
        if data.raw_content:
            structured = self._llm_structure_report(data.raw_content)
            if structured:
                data.content = structured.get("content") or data.content or data.raw_content
                if not data.key_progress and structured.get("key_progress"):
                    data.key_progress = structured["key_progress"]
                if not data.risks and structured.get("risks"):
                    data.risks = structured["risks"]
                if not data.next_plan and structured.get("next_plan"):
                    data.next_plan = structured["next_plan"]
            elif not data.content:
                data.content = data.raw_content

        report = EmployeeDailyReport(**data.model_dump())
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def _llm_structure_report(self, raw: str) -> Optional[dict]:
        """调用大模型将口述日报原文整理为结构化 JSON"""
        system = (
            "你是员工日报整理助手。将口述的当日工作原文整理为结构化 JSON：\n"
            "{\"content\":\"整理后的日报正文（书面语）\","
            "\"key_progress\":[\"关键进展1\",\"关键进展2\"],"
            "\"risks\":[\"风险或阻塞1\"],"
            "\"next_plan\":\"下一步计划\"}\n"
            "规则：key_progress/risks 为字符串数组，没有则给空数组；只返回 JSON。"
        )
        return _crm_llm_json(system, raw)

    def summarize_reports(self, reports: List[EmployeeDailyReport]) -> Optional[str]:
        """对员工日报列表生成 LLM 摘要（可选 ai_summary 用）"""
        if not reports:
            return None
        lines = [
            f"- 员工{r.employee_id}：进展[{'、'.join(r.key_progress or []) or '无'}]；"
            f"风险[{'、'.join(r.risks or []) or '无'}]"
            for r in reports[:30]
        ]
        system = "你是团队主管助理。用 3-5 句话总结以下员工日报的整体进展、风险与重点，120字以内。"
        return _crm_llm_text(system, "\n".join(lines))

    def generate_report_brief(self, report_id: int) -> Optional[str]:
        """对单份日报生成 LLM 简报"""
        report = self.get_report(report_id)
        if not report:
            return None
        ctx = (
            f"员工{report.employee_id} 的日报（{report.report_date}）：\n"
            f"正文：{report.content or '无'}\n"
            f"关键进展：{'、'.join(report.key_progress or []) or '无'}\n"
            f"风险：{'、'.join(report.risks or []) or '无'}\n"
            f"下一步：{report.next_plan or '无'}"
        )
        system = "你是主管助理。对这份员工日报生成一段简短点评（亮点+需关注点），80字以内。"
        return _crm_llm_text(system, ctx)

    def get_report(self, report_id: int) -> Optional[EmployeeDailyReport]:
        return self.db.query(EmployeeDailyReport).filter(
            EmployeeDailyReport.id == report_id
        ).first()

    def list_reports(
        self,
        employee_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[EmployeeDailyReport]:
        """条件查询日报列表（所有参数可选，不传则不做对应过滤）"""
        query = self.db.query(EmployeeDailyReport)

        if employee_id:
            query = query.filter(EmployeeDailyReport.employee_id == employee_id)
        if start_date:
            query = query.filter(EmployeeDailyReport.report_date >= start_date)
        if end_date:
            query = query.filter(EmployeeDailyReport.report_date <= end_date)
        # 动态拼接过滤条件：只对实际传入的参数添加 WHERE 子句

        return query.order_by(EmployeeDailyReport.report_date.desc()).all()

    def get_summary(
        self, report_date: date,
    ) -> DailyReportManagementSummary:
        """
        日报汇总（管理层用）
        - 统计指定日期的日报提交情况
        - 汇总每个员工的关键进展和风险
        - 调用 LLM 生成整体工作总览 ai_overview（不可用时为空）
        """
        query = self.db.query(EmployeeDailyReport).filter(
            EmployeeDailyReport.report_date == report_date
        )

        reports = query.all()

        employees = [
            EmployeeSummaryItem(
                employee_id=r.employee_id,
                key_progress=r.key_progress or [],
                risks=r.risks or [],
            )
            for r in reports
        ]
        # 列表推导式：将每条日报记录转为汇总条目，提取管理层关心的关键字段

        ai_overview = self._llm_daily_overview(employees) or ""
        return DailyReportManagementSummary(
            report_date=report_date,
            total_submitted=len(reports),
            employees=employees,
            ai_overview=ai_overview,
        )

    def _llm_daily_overview(self, employees: List[EmployeeSummaryItem]) -> Optional[str]:
        """调用 LLM 基于团队日报生成整体工作总览"""
        if not employees:
            return None
        lines = [
            f"- 员工{e.employee_id}：进展[{'、'.join(e.key_progress or []) or '无'}]；"
            f"风险[{'、'.join(e.risks or []) or '无'}]"
            for e in employees
        ]
        system = "你是管理层助理。基于以下团队日报，生成一段整体工作总览（进展亮点+主要风险+建议关注），150字以内。"
        return _crm_llm_text(system, "\n".join(lines))


# ============================================================
# 企业助手 - 智能对话（原 assistant_service 下沉）
# ============================================================
# 数据驱动设计：新增 API 只需在列表中添加一项，无需改核心逻辑。

API_REGISTRY: List[Dict[str, Any]] = [
    # ==================== 客户管理 ====================
    {
        "id": "list_leads",
        "name": "查询意向客户列表",
        "description": "查询客户列表，支持按状态、负责人、关键词筛选。可分页。",
        "method": "GET",
        "path": "/api/v1/crm/leads",
        "parameters": {
            "status": {"type": "string", "required": False, "description": "状态筛选: new/contacting/qualified/signed/lost"},
            "owner_employee_id": {"type": "int", "required": False, "description": "负责人 ID"},
            "keyword": {"type": "string", "required": False, "description": "关键词（姓名/联系方式）"},
            "page": {"type": "int", "required": False, "description": "页码，默认 1"},
            "page_size": {"type": "int", "required": False, "description": "每页条数，默认 20"},
        },
    },
    {
        "id": "get_lead",
        "name": "查询单个客户详情",
        "description": "根据客户 ID 查询客户详细信息。",
        "method": "GET",
        "path": "/api/v1/crm/leads/{id}",
        "parameters": {
            "id": {"type": "int", "required": True, "description": "客户 ID"},
        },
    },
    {
        "id": "create_lead",
        "name": "新增意向客户",
        "description": "录入一个新的意向客户。customer_name 和 owner_employee_id 必填。",
        "method": "POST",
        "path": "/api/v1/crm/leads",
        "parameters": {
            "customer_name": {"type": "string", "required": True, "description": "客户姓名"},
            "contact_info": {"type": "string", "required": False, "description": "联系方式"},
            "education_level": {"type": "string", "required": False, "description": "学历层次"},
            "intended_country": {"type": "string", "required": False, "description": "意向国家"},
            "intended_major": {"type": "string", "required": False, "description": "意向专业"},
            "source_channel": {"type": "string", "required": False, "description": "来源渠道"},
            "background_info": {"type": "string", "required": False, "description": "背景说明"},
            "remark": {"type": "string", "required": False, "description": "备注"},
            "owner_employee_id": {"type": "int", "required": True, "description": "负责员工 ID"},
        },
    },
    {
        "id": "update_lead",
        "name": "更新客户信息",
        "description": "更新客户的基本信息（部分更新）。",
        "method": "PUT",
        "path": "/api/v1/crm/leads/{id}",
        "parameters": {
            "id": {"type": "int", "required": True, "description": "客户 ID"},
            "customer_name": {"type": "string", "required": False, "description": "客户姓名"},
            "contact_info": {"type": "string", "required": False, "description": "联系方式"},
            "education_level": {"type": "string", "required": False, "description": "学历"},
            "intended_country": {"type": "string", "required": False, "description": "意向国家"},
            "intended_major": {"type": "string", "required": False, "description": "意向专业"},
            "remark": {"type": "string", "required": False, "description": "备注"},
        },
    },
    {
        "id": "update_lead_status",
        "name": "更新客户状态",
        "description": "更新客户的销售状态。状态流转有规则限制。",
        "method": "PUT",
        "path": "/api/v1/crm/leads/{id}/status",
        "parameters": {
            "id": {"type": "int", "required": True, "description": "客户 ID"},
            "status": {"type": "string", "required": True, "description": "目标状态: new/contacting/qualified/signed/lost"},
            "lost_reason": {"type": "string", "required": False, "description": "流失原因（状态为 lost 时必填）"},
        },
    },
    # ==================== 跟进记录 ====================
    {
        "id": "create_follow_up",
        "name": "新增跟进记录",
        "description": "为客户添加一条跟进记录。",
        "method": "POST",
        "path": "/api/v1/crm/leads/{lead_id}/follow-ups",
        "parameters": {
            "lead_id": {"type": "int", "required": True, "description": "客户 ID"},
            "employee_id": {"type": "int", "required": True, "description": "跟进员工 ID"},
            "follow_type": {"type": "string", "required": True, "description": "跟进方式: phone/wechat/meeting/email/other"},
            "content": {"type": "string", "required": True, "description": "跟进内容"},
            "next_plan": {"type": "string", "required": False, "description": "下次计划"},
        },
    },
    {
        "id": "list_follow_ups",
        "name": "查询跟进记录",
        "description": "查询某个客户的所有跟进记录。",
        "method": "GET",
        "path": "/api/v1/crm/leads/{lead_id}/follow-ups",
        "parameters": {
            "lead_id": {"type": "int", "required": True, "description": "客户 ID"},
        },
    },
    # ==================== 员工日报 ====================
    {
        "id": "create_daily_report",
        "name": "提交日报",
        "description": "提交员工日报。可只传 raw_content，系统自动填充 content。",
        "method": "POST",
        "path": "/api/v1/employee/daily-reports",
        "parameters": {
            "employee_id": {"type": "int", "required": True, "description": "员工 ID"},
            "report_date": {"type": "string", "required": True, "description": "日报日期，格式 YYYY-MM-DD"},
            "raw_content": {"type": "string", "required": False, "description": "口述原文"},
            "content": {"type": "string", "required": False, "description": "结构化内容"},
            "key_progress": {"type": "array", "required": False, "description": "关键进展列表"},
            "risks": {"type": "array", "required": False, "description": "风险项列表"},
            "next_plan": {"type": "string", "required": False, "description": "明日计划"},
        },
    },
    {
        "id": "list_daily_reports",
        "name": "查询日报列表",
        "description": "查询日报列表，支持按员工和日期筛选。",
        "method": "GET",
        "path": "/api/v1/employee/daily-reports",
        "parameters": {
            "employee_id": {"type": "int", "required": False, "description": "员工 ID"},
            "start_date": {"type": "string", "required": False, "description": "起始日期"},
            "end_date": {"type": "string", "required": False, "description": "截止日期"},
        },
    },
    {
        "id": "daily_report_summary",
        "name": "日报汇总",
        "description": "查看某天的日报汇总（管理层用）。",
        "method": "GET",
        "path": "/api/v1/employee/daily-reports/summary",
        "parameters": {
            "report_date": {"type": "string", "required": True, "description": "汇总日期，格式 YYYY-MM-DD"},
        },
    },
]

# 将注册表转为字典，方便按 ID 查找
API_REGISTRY_DICT = {api["id"]: api for api in API_REGISTRY}


# ============================================================
# NL2SQL 引擎
# ============================================================

# 允许查询的表白名单
SQL_TABLE_WHITELIST = {
    "crm_lead",
    "crm_follow_up",
    "employee_daily_report",
}

# SQL 关键词黑名单
SQL_KEYWORD_BLACKLIST = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "REPLACE", "MERGE", "CALL",
    "EXEC", "EXECUTE", "INTO", "VALUES",
}

# 表结构描述（提供给 LLM）
CRM_TABLE_SCHEMA = """
表 1: crm_lead（意向客户表）
字段:
  - id: 主键
  - customer_name: 客户姓名
  - contact_info: 联系方式
  - gender: 性别（M/F/U）
  - age: 年龄
  - education_level: 学历层次
  - intended_country: 意向国家
  - intended_major: 意向专业
  - source_channel: 来源渠道
  - status: 销售状态（new/contacting/qualified/signed/lost）
  - lost_reason: 流失原因
  - owner_employee_id: 负责员工 ID
  - last_contact_time: 最后联系时间
  - create_time: 创建时间
  - update_time: 更新时间

表 2: crm_follow_up（跟进记录表）
字段:
  - id: 主键
  - lead_id: 客户 ID
  - employee_id: 跟进员工 ID
  - follow_type: 跟进方式（phone/wechat/meeting/email/other）
  - content: 跟进内容
  - next_plan: 下次计划
  - create_time: 创建时间

表 3: employee_daily_report（员工日报表）
字段:
  - id: 主键
  - employee_id: 员工 ID
  - report_date: 日报日期
  - status: 状态（draft/submitted）
  - raw_content: 原始口述内容
  - content: 结构化内容
  - key_progress: 关键进展（JSON 数组）
  - risks: 风险项（JSON 数组）
  - next_plan: 明日计划
  - create_time: 创建时间
"""


def _generate_sql(user_message: str) -> Optional[str]:
    """调用 LLM 生成 SQL 查询语句。"""

    system_prompt = f"""你是一个 SQL 生成助手。根据用户的自然语言问题，生成 MySQL 查询语句。

数据库表结构:
{CRM_TABLE_SCHEMA}

规则:
1. 只能生成 SELECT 查询，禁止 INSERT/UPDATE/DELETE 等操作
2. 只能查询以下表: crm_lead, crm_follow_up, employee_daily_report
3. 使用标准 MySQL 语法
4. 合理使用 WHERE、ORDER BY、LIMIT 等子句
5. LIKE 模糊查询使用 %关键词% 格式
6. 日期比较使用 DATE() 函数或直接比较
7. 不要使用子查询和 UNION

返回格式要求（必须是有效 JSON）:
{{"sql": "SELECT ... FROM ... WHERE ..."}}

示例:
用户问题: "有多少个联系中的客户"
返回: {{\"sql\": \"SELECT COUNT(*) AS count FROM crm_lead WHERE status = 'contacting'\"}}

用户问题: "最近一周新增的客户"
返回: {{\"sql\": \"SELECT * FROM crm_lead WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) ORDER BY create_time DESC LIMIT 20\"}}"""

    raw_text = _call_llm(system_prompt, user_message)
    if not raw_text:
        return None

    result = _extract_json(raw_text)
    if not result or "sql" not in result:
        logger.warning("LLM 未返回有效的 SQL")
        return None

    return result["sql"]


def _validate_sql(sql: str) -> Tuple[bool, str]:
    """
    校验 SQL 语句安全性。

    返回: (是否通过, 错误消息)
    """
    sql_upper = sql.upper().strip()

    # 1. 检查关键词黑名单
    for keyword in SQL_KEYWORD_BLACKLIST:
        # 使用正则匹配独立单词，避免误判（如 SELECT 不应匹配到 "SELECTED"）
        if re.search(rf"\b{keyword}\b", sql_upper):
            return False, f"禁止使用的关键词: {keyword}"

    # 2. 检查表白名单
    # 提取 SQL 中出现的表名
    tables_found = re.findall(r"\bFROM\s+(\w+)", sql_upper)
    tables_found += re.findall(r"\bJOIN\s+(\w+)", sql_upper)

    for table in tables_found:
        if table.lower() not in SQL_TABLE_WHITELIST:
            return False, f"禁止查询的表: {table}"

    # 3. 只允许 SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "只允许 SELECT 查询"

    # 4. 禁止 UNION
    if "UNION" in sql_upper:
        return False, "禁止使用 UNION"

    # 5. 禁止分号（防止多语句注入）
    if ";" in sql:
        return False, "禁止多语句执行"

    return True, ""


def _execute_sql(db: Session, sql: str) -> Tuple[List[Dict], str]:
    """
    执行 SQL 查询。

    返回: (结果列表, 错误消息)
    """
    try:
        # 自动追加 LIMIT 100
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 100"

        result = db.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()

        # 转为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # 处理特殊类型
                if isinstance(val, Decimal):
                    val = float(val)
                elif isinstance(val, datetime):
                    val = val.isoformat()
                row_dict[col] = val
            data.append(row_dict)

        return data, ""

    except Exception as e:
        logger.error(f"SQL 执行失败: {e}")
        return [], str(e)


def _format_sql_result(user_message: str, sql: str, data: List[Dict]) -> str:
    """调用 LLM 将 SQL 查询结果格式化为自然语言回复。"""

    system_prompt = """你是一个数据分析师助手。根据用户的原始问题和 SQL 查询结果，生成清晰的自然语言回复。

规则:
1. 用简洁的中文回答用户问题
2. 如果结果为空，说明没有找到匹配的数据
3. 如果有多条记录，可以列举关键信息或总结
4. 数字要准确，不要编造数据"""

    user_content = f"""用户问题: {user_message}

执行的 SQL:
{sql}

查询结果（JSON）:
{json.dumps(data[:10], ensure_ascii=False, indent=2)}
{"（结果已截断，仅显示前 10 条）" if len(data) > 10 else ""}

请生成自然语言回复。"""

    return _call_llm(system_prompt, user_content) or "查询完成，但格式化失败。"


# ============================================================
# NL2API 引擎
# ============================================================

def _select_api(user_message: str) -> Optional[Dict]:
    """
    调用 LLM 从注册表选择 API 并提取参数。

    返回: {"api_id": "...", "params": {...}}
    """
    # 构造 API 描述
    api_list_text = "\n".join([
        f"- {api['id']}: {api['name']} — {api['description']}"
        for api in API_REGISTRY
    ])

    system_prompt = f"""你是一个 API 路由助手。根据用户的自然语言请求，选择最合适的 API 并提取参数。

可用 API 列表:
{api_list_text}

规则:
1. 根据用户意图选择最匹配的 API
2. 从用户消息中提取参数值
3. 如果用户没有提供某个必填参数，参数值设为 null
4. 返回有效的 JSON 格式

返回格式:
{{"api_id": "API_ID", "params": {{参数名: 值, ...}}}}

示例:
用户: "帮我录入一个新客户叫张三，手机号 13800138000，负责人是 2 号"
返回: {{\"api_id\": \"create_lead\", \"params\": {{\"customer_name\": \"张三\", \"contact_info\": \"13800138000\", \"owner_employee_id\": 2}}}}"""

    raw_text = _call_llm(system_prompt, user_message)
    if not raw_text:
        return None

    result = _extract_json(raw_text)
    if not result or "api_id" not in result:
        logger.warning("LLM 未返回有效的 API 选择")
        return None

    return result


def _execute_api(db: Session, api_id: str, params: Dict) -> Tuple[Any, str]:
    """
    执行 API 调用（内部调用 Service 层）。

    返回: (执行结果, 错误消息)
    """
    if api_id not in API_REGISTRY_DICT:
        return None, f"未知的 API: {api_id}"

    api_config = API_REGISTRY_DICT[api_id]

    try:
        # ==================== 客户管理 ====================
        if api_id == "list_leads":
            service = CrmService(db)
            from schemas.crm import LeadListResponse
            from datetime import date as date_type
            result = service.list_leads(
                status=params.get("status"),
                owner_employee_id=params.get("owner_employee_id"),
                keyword=params.get("keyword"),
                page=params.get("page", 1),
                page_size=params.get("page_size", 20),
            )
            return result.model_dump(mode="json"), ""

        elif api_id == "get_lead":
            service = CrmService(db)
            lead = service.get_lead(params["id"])
            if not lead:
                return None, "客户不存在"
            from schemas.crm import LeadResponse
            return LeadResponse.model_validate(lead).model_dump(mode="json"), ""

        elif api_id == "create_lead":
            from schemas.crm import LeadCreate
            service = CrmService(db)
            data = LeadCreate(**params)
            lead = service.create_lead(data)
            from schemas.crm import LeadResponse
            return LeadResponse.model_validate(lead).model_dump(mode="json"), ""

        elif api_id == "update_lead":
            from schemas.crm import LeadUpdate
            service = CrmService(db)
            lead_id = params.pop("id")
            data = LeadUpdate(**params)
            lead = service.update_lead(lead_id, data)
            if not lead:
                return None, "客户不存在"
            from schemas.crm import LeadResponse
            return LeadResponse.model_validate(lead).model_dump(mode="json"), ""

        elif api_id == "update_lead_status":
            from schemas.crm import LeadStatusUpdate
            service = CrmService(db)
            lead_id = params.pop("id")
            data = LeadStatusUpdate(**params)
            lead = service.update_lead_status(lead_id, data)
            from schemas.crm import LeadResponse
            return LeadResponse.model_validate(lead).model_dump(mode="json"), ""

        # ==================== 跟进记录 ====================
        elif api_id == "create_follow_up":
            from schemas.crm import FollowUpCreate
            service = CrmService(db)
            lead_id = params.pop("lead_id")
            data = FollowUpCreate(**params)
            follow_up = service.create_follow_up(lead_id, data)
            from schemas.crm import FollowUpResponse
            return FollowUpResponse.model_validate(follow_up).model_dump(mode="json"), ""

        elif api_id == "list_follow_ups":
            service = CrmService(db)
            follow_ups = service.list_follow_ups(params["lead_id"])
            from schemas.crm import FollowUpResponse
            return [FollowUpResponse.model_validate(f).model_dump(mode="json") for f in follow_ups], ""

        # ==================== 员工日报 ====================
        elif api_id == "create_daily_report":
            from schemas.crm import DailyReportCreate
            from datetime import datetime as dt
            service = EmployeeService(db)
            # 处理日期格式
            if "report_date" in params and isinstance(params["report_date"], str):
                params["report_date"] = dt.strptime(params["report_date"], "%Y-%m-%d").date()
            data = DailyReportCreate(**params)
            report = service.create_report(data)
            from schemas.crm import DailyReportResponse
            return DailyReportResponse.model_validate(report).model_dump(mode="json"), ""

        elif api_id == "list_daily_reports":
            from datetime import datetime as dt
            service = EmployeeService(db)
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            if start_date:
                start_date = dt.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end_date = dt.strptime(end_date, "%Y-%m-%d").date()
            reports = service.list_reports(
                employee_id=params.get("employee_id"),
                start_date=start_date,
                end_date=end_date,
            )
            from schemas.crm import DailyReportResponse
            return [DailyReportResponse.model_validate(r).model_dump(mode="json") for r in reports], ""

        elif api_id == "daily_report_summary":
            from datetime import datetime as dt
            service = EmployeeService(db)
            report_date = dt.strptime(params["report_date"], "%Y-%m-%d").date()
            result = service.get_summary(report_date=report_date)
            return result.model_dump(mode="json"), ""

        else:
            return None, f"API 未实现: {api_id}"

    except Exception as e:
        logger.error(f"API 执行失败: {api_id}, {e}")
        return None, str(e)


def _format_api_result(user_message: str, api_id: str, result: Any) -> str:
    """调用 LLM 将 API 执行结果格式化为自然语言回复。"""

    api_config = API_REGISTRY_DICT.get(api_id, {})

    system_prompt = """你是一个助手。根据用户的原始请求和 API 执行结果，生成清晰的自然语言回复。

规则:
1. 用简洁的中文回复
2. 确认操作是否成功
3. 如果有创建/更新的数据，说明关键信息
4. 如果有错误，解释原因"""

    user_content = f"""用户请求: {user_message}

调用的 API: {api_id} — {api_config.get('name', '')}

执行结果:
{json.dumps(result, ensure_ascii=False, indent=2, default=str) if result else '无'}

请生成自然语言回复。"""

    return _call_llm(system_prompt, user_content) or "操作完成。"


# ============================================================
# 意图识别与核心编排
# ============================================================

INTENT_SYSTEM_PROMPT = """你是一个意图识别助手。分析用户消息，判断用户想要做什么。

用户可能的意图类型:
1. sql — 查询数据（如"有多少客户"、"最近一周新增了几个"、"看看客户 3 号的信息"）
2. api — 执行操作（如"帮我录入新客户"、"更新客户状态"、"提交日报"）
3. text — 闲聊或其他（如"你好"、"谢谢"、"你是谁"）

规则:
1. 如果用户想查数据、看报表，返回 sql
2. 如果用户想新增、修改、删除数据，返回 api
3. 其他情况返回 text

返回格式（必须是有效 JSON）:
{"intent": "sql" 或 "api" 或 "text"}

示例:
用户: "现在有多少个联系中的客户"
返回: {"intent": "sql"}

用户: "帮我录入一个新客户叫王五"
返回: {"intent": "api"}

用户: "你好"
返回: {"intent": "text"}"""


class AssistantService:
    """企业助手 - 智能对话服务（NL2SQL / NL2API / 闲聊）"""

    def __init__(self, db: Session):
        self.db = db

    def chat(self, request: AssistantChatRequest, employee_id: int) -> AssistantChatResponse:
        """
        处理聊天请求。

        流程:
          1. 获取或创建会话
          2. 保存用户消息
          3. 意图识别
          4. 路由执行（SQL/API/Text）
          5. 保存助手回复
          6. 返回响应
        """
        # 1. 获取或创建会话
        session = self._get_or_create_session(request, employee_id)

        # 2. 保存用户消息
        user_message = AssistantMessage(
            session_id=session.session_id,
            role="user",
            content=request.message,
        )
        self.db.add(user_message)
        self.db.commit()

        # 3. 意图识别
        intent_result = self._recognize_intent(request.message)
        intent = intent_result.get("intent", "text")

        # 4. 路由执行
        reply_text = ""
        action_type = None
        action_data = None
        action_detail = None

        if intent == "sql":
            # NL2SQL 路径
            reply_text, action_data, action_detail = self._handle_sql_intent(request.message)
            action_type = "sql"

        elif intent == "api":
            # NL2API 路径
            reply_text, action_data, action_detail = self._handle_api_intent(request.message)
            action_type = "api"

        else:
            # 闲聊路径
            reply_text = self._handle_text_intent(request.message)
            action_type = "text"

        # 5. 保存助手回复
        assistant_message = AssistantMessage(
            session_id=session.session_id,
            role="assistant",
            content=reply_text,
            action_type=action_type,
            action_detail=action_detail,
            action_result=action_data,
        )
        self.db.add(assistant_message)

        # 更新会话最后消息时间
        session.last_message_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(assistant_message)

        # 6. 返回响应
        return AssistantChatResponse(
            session_id=session.session_id,
            reply_text=reply_text,
            action_type=action_type,
            action_data=action_data,
            create_time=assistant_message.create_time,
        )

    def _get_or_create_session(self, request: AssistantChatRequest, employee_id: int) -> AssistantSession:
        """获取或创建会话。"""
        if request.session_id:
            # 尝试获取已有会话
            session = self.db.query(AssistantSession).filter(
                AssistantSession.session_id == request.session_id,
                AssistantSession.employee_id == employee_id,
            ).first()
            if session:
                return session

        # 创建新会话
        session = AssistantSession(
            session_id=f"asst_{uuid.uuid4().hex[:16]}",
            employee_id=employee_id,
            status="active",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _recognize_intent(self, message: str) -> Dict:
        """识别用户意图。"""
        raw_text = _call_llm(INTENT_SYSTEM_PROMPT, message)
        if not raw_text:
            return {"intent": "text"}

        result = _extract_json(raw_text)
        if not result:
            return {"intent": "text"}

        return result

    def _handle_sql_intent(self, message: str) -> Tuple[str, Optional[Dict], Optional[Dict]]:
        """处理 SQL 意图。返回: (回复文本, 结果数据, 详情)"""
        # 1. 生成 SQL
        sql = _generate_sql(message)
        if not sql:
            return "抱歉，我无法理解您的查询请求，请换种说法试试。", None, None

        # 2. 安全校验
        is_valid, error_msg = _validate_sql(sql)
        if not is_valid:
            logger.warning(f"SQL 校验失败: {error_msg}")
            return f"抱歉，查询请求包含不允许的操作：{error_msg}", None, {"sql": sql, "error": error_msg}

        # 3. 执行查询
        data, exec_error = _execute_sql(self.db, sql)
        if exec_error:
            return f"查询执行失败：{exec_error}", None, {"sql": sql, "error": exec_error}

        # 4. 格式化回复
        reply_text = _format_sql_result(message, sql, data)

        return reply_text, {"rows": data, "count": len(data)}, {"sql": sql}

    def _handle_api_intent(self, message: str) -> Tuple[str, Optional[Dict], Optional[Dict]]:
        """处理 API 意图。返回: (回复文本, 结果数据, 详情)"""
        # 1. 选择 API + 提取参数
        api_result = _select_api(message)
        if not api_result:
            return "抱歉，我无法理解您的请求，请换种说法试试。", None, None

        api_id = api_result.get("api_id")
        params = api_result.get("params", {})

        # 2. 执行 API
        result, error = _execute_api(self.db, api_id, params)
        if error:
            return f"操作失败：{error}", None, {"api_id": api_id, "params": params, "error": error}

        # 3. 格式化回复
        reply_text = _format_api_result(message, api_id, result)

        return reply_text, result, {"api_id": api_id, "params": params}

    def _handle_text_intent(self, message: str) -> str:
        """处理闲聊意图。"""
        system_prompt = """你是一个友好的企业智能助手。你是公司内部的 AI 助手，帮助员工查询数据、执行操作。

规则:
1. 用简洁友好的中文回复
2. 如果用户想查询数据或执行操作，引导他们描述具体需求
3. 不要编造数据或承诺你做不到的事情"""

        reply = _call_llm(system_prompt, message)
        return reply or "我在，请问有什么可以帮您？"

    def list_sessions(self, employee_id: int) -> List[AssistantSessionResponse]:
        """查询员工的会话列表。"""
        sessions = self.db.query(AssistantSession).filter(
            AssistantSession.employee_id == employee_id
        ).order_by(AssistantSession.last_message_time.desc()).limit(20).all()

        return [AssistantSessionResponse.model_validate(s) for s in sessions]

    def list_messages(self, session_id: str, employee_id: int) -> List[AssistantMessageResponse]:
        """查询会话消息历史。"""
        # 校验会话归属
        session = self.db.query(AssistantSession).filter(
            AssistantSession.session_id == session_id,
            AssistantSession.employee_id == employee_id,
        ).first()
        if not session:
            return []

        messages = self.db.query(AssistantMessage).filter(
            AssistantMessage.session_id == session_id
        ).order_by(AssistantMessage.create_time.asc()).all()

        return [AssistantMessageResponse.model_validate(m) for m in messages]