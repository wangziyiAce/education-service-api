"""智能报告助手 — 证据化回答编排。

本模块负责将工具结果和 LLM 能力结合，生成可信的自然语言回答。

Iteration 2A 策略：
1. LLM 可用时 → 通过 evidence map + 结构化提示生成回答，并校验数字
2. LLM 不可用时 → 确定性模板降级

核心安全约束：
- LLM 不能直接访问数据库或业务指标
- 所有数字来自工具结果
- 回答中的数字必须能追溯到证据
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from services.reporting.assistant.guardrails import (
    build_evidence_map,
    extract_allowed_numbers_from_tool_results,
    validate_numbers_in_answer,
)
from services.reporting.assistant.schemas import (
    AssistantToolResult,
    EvidenceItem,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 回答生成入口
# ---------------------------------------------------------------------------


def compose_answer(
    *,
    intent: str,
    tool_results: list[AssistantToolResult],
    data_quality_level: str = "ok",
    llm_enabled: bool = False,
) -> dict[str, Any]:
    """根据意图和工具结果生成回答。

    Args:
        intent: 用户意图。
        tool_results: 所有工具调用结果列表。
        data_quality_level: 数据质量等级。
        llm_enabled: LLM 是否可用。

    Returns:
        dict 包含 answer、evidence、suggested_follow_ups。
    """
    # 提取所有工具的成功结果数据
    tool_data_list = [r.data for r in tool_results if r.status == "success"]

    # 构建证据映射
    evidence_map = build_evidence_map(tool_data_list)
    allowed_numbers = extract_allowed_numbers_from_tool_results(tool_data_list)

    if llm_enabled:
        answer, evidence = _compose_with_llm(
            intent=intent,
            tool_data_list=tool_data_list,
            evidence_map=evidence_map,
            allowed_numbers=allowed_numbers,
        )
    else:
        answer, evidence = _compose_deterministic(
            intent=intent,
            tool_data_list=tool_data_list,
        )

    # 注入数据质量限制
    from services.reporting.assistant.guardrails import apply_data_quality_guardrail
    is_analysis = intent in ("drill_down", "explain_risk", "explain_metric")
    answer = apply_data_quality_guardrail(
        answer=answer,
        data_quality_level=data_quality_level,
        is_analysis=is_analysis,
    )

    # 生成建议追问
    suggested_follow_ups = _generate_follow_ups(intent, tool_data_list)

    return {
        "answer": answer,
        "evidence": evidence,
        "suggested_follow_ups": suggested_follow_ups,
    }


# ---------------------------------------------------------------------------
# LLM 模式
# ---------------------------------------------------------------------------


def _compose_with_llm(
    *,
    intent: str,
    tool_data_list: list[Any],
    evidence_map: dict[str, Any],
    allowed_numbers: set[float | int],
) -> tuple[str, list[dict[str, Any]]]:
    """使用 LLM 生成自然语言回答，并校验数字。"""
    try:
        from services.reporting.llm_client import ReportLLMClient

        system_prompt = _build_answer_system_prompt(intent, tool_data_list, evidence_map)
        user_prompt = "请根据上述数据生成用户友好的中文回答。"

        client = ReportLLMClient()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = client.chat_completion(messages, temperature=0.3, max_tokens=600)

        if response.status != "success" or not response.content:
            logger.warning("LLM 回答生成失败，降级到确定性模板")
            return _compose_deterministic(intent=intent, tool_data_list=tool_data_list)

        raw_answer = response.content.strip()

        # 数字校验
        is_valid, hallucinated = validate_numbers_in_answer(
            answer=raw_answer,
            allowed_numbers=allowed_numbers,
        )

        if not is_valid:
            logger.warning("LLM 回答包含幻觉数字: %s", hallucinated)
            # 尝试一次修复
            repair_prompt = (
                f"上述回答中包含不在允许列表中的数字：{hallucinated}。\n"
                f"允许的数字: {sorted(allowed_numbers)}\n"
                "请修改回答，只使用允许列表中的数字。"
            )
            repair_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": raw_answer},
                {"role": "user", "content": repair_prompt},
            ]
            repair_response = client.chat_completion(repair_messages, temperature=0.1, max_tokens=600)

            if repair_response.status == "success" and repair_response.content:
                raw_answer = repair_response.content.strip()
                is_valid, _ = validate_numbers_in_answer(
                    answer=raw_answer,
                    allowed_numbers=allowed_numbers,
                )

            if not is_valid:
                logger.warning("修复后仍包含幻觉数字，使用确定性模板")
                return _compose_deterministic(intent=intent, tool_data_list=tool_data_list)

        # 构建证据
        evidence = _build_evidence_from_map(evidence_map)

        return raw_answer, evidence

    except Exception as exc:
        logger.warning("LLM 回答生成异常: %s，降级到确定性模板", exc)
        return _compose_deterministic(intent=intent, tool_data_list=tool_data_list)


def _build_answer_system_prompt(
    intent: str,
    tool_data_list: list[Any],
    evidence_map: dict[str, Any],
) -> str:
    """构建 LLM 回答生成的 System Prompt。"""
    # 整理证据索引
    evidence_lines = []
    for key, value in evidence_map.items():
        evidence_lines.append(f"[{key}] {value}")

    evidence_text = "\n".join(evidence_lines) if evidence_lines else "（无额外数据）"

    # 工具数据摘要
    data_summary = _summarize_tool_data(tool_data_list)

    return (
        "你是海外留学教育服务平台的智能报告助手。\n\n"
        "**回答规则（必须严格遵守）：**\n"
        "1. 只能使用以下证据中提供的数字，不得编造任何数字。\n"
        "2. 使用 `{{E1}}` `{{E2}}` 占位符引用证据数字，不要直接写数值。\n"
        "3. 工具数据中的文字结论可以引用，但不能编造数据中不存在的风险原因。\n"
        "4. 行动建议必须标明是\"建议\"，不能表述为确定性事实。\n"
        "5. 回答使用中文，简洁、结构清晰。\n"
        "6. 如果数据包含多个实体，使用列表格式，每个实体说明 risk_score 和关键原因。\n\n"
        f"**当前意图**: {intent}\n\n"
        f"**证据索引**:\n{evidence_text}\n\n"
        f"**工具数据**:\n{data_summary}\n"
    )


def _summarize_tool_data(tool_data_list: list[Any]) -> str:
    """将工具数据转为 LLM 可读的摘要。"""
    parts = []
    for i, data in enumerate(tool_data_list):
        if not isinstance(data, dict):
            continue
        # 移除嵌套的 referered_entities（太长，用摘要替代）
        safe = dict(data)
        if "referenced_entities" in safe:
            safe["referenced_entities_count"] = len(safe.pop("referenced_entities", []))
        if "metric_traces" in safe:
            safe["metric_traces_count"] = len(safe.pop("metric_traces", []))
        # 截断内容
        safe_str = str(safe)
        if len(safe_str) > 800:
            safe_str = safe_str[:800] + "..."
        parts.append(f"[工具结果 {i+1}] {safe_str}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 确定性模板降级
# ---------------------------------------------------------------------------


def _compose_deterministic(
    *,
    intent: str,
    tool_data_list: list[Any],
) -> tuple[str, list[dict[str, Any]]]:
    """LLM 不可用时使用确定性模板生成回答。"""
    if intent == "query_report_status":
        return _template_status(tool_data_list)
    elif intent == "drill_down":
        return _template_drill_down(tool_data_list)
    elif intent == "explain_risk":
        return _template_explain_risk(tool_data_list)
    elif intent == "explain_metric":
        return _template_explain_metric(tool_data_list)
    elif intent == "query_data_quality":
        return _template_data_quality(tool_data_list)
    else:
        return _template_generic(tool_data_list)


def _template_status(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    data = tool_data_list[0] if tool_data_list else {}
    status = data.get("status", "unknown")
    status_text = {
        "pending": "排队等待生成",
        "generating": "正在生成中",
        "completed": "已完成",
        "failed": "生成失败",
    }.get(status, status)

    answer = f"报告 #{data.get('report_id')} 当前状态：{status_text}。"
    if data.get("suggest_retry"):
        answer += " 建议使用重试功能重新生成。"

    evidence = [{"source": "query_report_status", "reference": f"report_id={data.get('report_id')}", "value": status}]
    return answer, evidence


def _template_drill_down(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    data = tool_data_list[0] if tool_data_list else {}
    items = data.get("items", [])
    if not items:
        return "当前没有风险明细数据。", []

    lines = [f"当前风险最高的 {len(items)} 个申请："]
    evidence = []
    for i, item in enumerate(items):
        app_id = item.get("application_id", "?")
        score = item.get("risk_score", 0)
        level = item.get("risk_level", "?")
        reasons = item.get("risk_reasons", [])
        reasons_text = "、".join(reasons[:3]) if reasons else "无详细原因"
        lines.append(f"{i+1}. 申请 #{app_id}：风险分 {score}（{level}），{reasons_text}")
        evidence.append({"source": "get_application_risk_items", "reference": f"application_id={app_id}", "value": score})

    answer = "\n".join(lines)
    return answer, evidence


def _template_explain_risk(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    data = tool_data_list[0] if tool_data_list else {}
    risk_reasons = data.get("risk_reasons", [])
    score = data.get("risk_score", 0)
    level = data.get("risk_level", "?")
    missing = data.get("missing_materials", [])
    next_action = data.get("next_action", "")

    parts = [f"申请 #{data.get('application_id')} 风险分为 {score}（{level}）。"]
    if risk_reasons:
        parts.append("风险原因：")
        for r in risk_reasons:
            parts.append(f"  - {r}")
    if missing:
        parts.append(f"缺失材料：{'、'.join(missing)}")
    if next_action:
        parts.append(f"建议：{next_action}")

    evidence = [{"source": "get_application_risk_detail", "reference": f"risk_score", "value": score}]
    return "\n".join(parts), evidence


def _template_explain_metric(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    data = tool_data_list[0] if tool_data_list else {}
    metric = data.get("metric_name", "?")
    formula = data.get("formula", "未提供")
    sources = data.get("source_tables", [])
    filters = data.get("filters", {})

    parts = [f"指标 '{metric}' 的追溯信息："]
    parts.append(f"  计算公式：{formula}")
    parts.append(f"  来源表：{', '.join(sources) if sources else '未指定'}")
    if filters:
        parts.append(f"  过滤条件：{filters}")

    evidence = [{"source": "get_metric_trace", "reference": f"metric={metric}", "value": formula}]
    return "\n".join(parts), evidence


def _template_data_quality(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    data = tool_data_list[0] if tool_data_list else {}
    level = data.get("level", "ok")
    desc = data.get("level_description", "未知")
    warnings = data.get("warnings", [])
    limitations = data.get("limitations", [])

    parts = [f"报告数据质量：{desc}"]
    if warnings:
        parts.append("注意事项：")
        for w in warnings:
            parts.append(f"  - {w}")
    if limitations:
        parts.append("当前限制：")
        for l in limitations:
            parts.append(f"  - {l}")

    evidence = [{"source": "get_report_data_quality", "reference": "level", "value": level}]
    return "\n".join(parts), evidence


def _template_generic(tool_data_list: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    return "已处理你的请求。", []


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


def _build_evidence_from_map(evidence_map: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"evidence_id": key, "label": f"证据 {key}", "value": value, "source": "tool_results"}
        for key, value in evidence_map.items()
    ]


def _generate_follow_ups(intent: str, tool_data_list: list[Any]) -> list[str]:
    """根据意图和数据生成建议追问。"""
    data = tool_data_list[0] if tool_data_list else {}

    follow_ups_map = {
        "drill_down": ["第一个为什么这么高？", "这个风险分怎么计算的？", "这个报告的数据可靠吗？"],
        "explain_risk": ["这个风险分怎么计算的？", "有哪些缺失材料需要补充？"],
        "explain_metric": ["受影响的有哪些申请？", "这个报告的数据可靠吗？"],
        "query_data_quality": ["最严重的是哪几个？", "有哪些需要注意的数据问题？"],
        "query_report_status": ["报告完成后可以查看哪些内容？"],
    }

    return follow_ups_map.get(intent, [])[:3]
