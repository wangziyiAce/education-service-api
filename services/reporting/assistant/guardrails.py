"""智能报告助手 — 安全护栏与数据质量约束。

本模块负责：
1. DataQuality 回答限制注入 — 根据数据质量等级限制回答内容
2. 数字防幻觉校验 — 确保 LLM 输出的数字全部可追溯到工具结果
3. 回答安全校验 — 防止越狱、敏感信息泄露

架构位置：
    LLM 回答草案 → Guardrail 校验 → 修复或降级 → 最终回答
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DataQuality 约束
# ---------------------------------------------------------------------------

_DATA_QUALITY_RULES: dict[str, dict[str, Any]] = {
    "ok": {
        "prefix": "",
        "can_analyze": True,
        "can_conclude": True,
        "must_warn": False,
    },
    "warning": {
        "prefix": "⚠️ 数据质量提示：部分可选数据源缺失，以下结论仅基于现有数据。",
        "can_analyze": True,
        "can_conclude": True,
        "must_warn": True,
    },
    "empty": {
        "prefix": "当前统计周期没有有效数据，无法判断趋势或分析变化原因。",
        "can_analyze": False,
        "can_conclude": False,
        "must_warn": True,
    },
    "degraded": {
        "prefix": "报告处于降级状态，以下内容仅供有限参考，不能作为强结论使用。",
        "can_analyze": True,
        "can_conclude": False,
        "must_warn": True,
    },
    "failed": {
        "prefix": "报告生成失败，不能基于该报告进行业务判断。建议使用重试功能重新生成。",
        "can_analyze": False,
        "can_conclude": False,
        "must_warn": True,
    },
}


def apply_data_quality_guardrail(
    *,
    answer: str,
    data_quality_level: str,
    is_analysis: bool = False,
) -> str:
    """根据数据质量等级对回答施加限制。

    Args:
        answer: 原始回答文本。
        data_quality_level: 数据质量等级（ok/warning/empty/degraded/failed）。
        is_analysis: 是否是业务分析类回答（vs 状态查询）。

    Returns:
        施加限制后的回答文本。
    """
    rules = _DATA_QUALITY_RULES.get(data_quality_level, _DATA_QUALITY_RULES["ok"])

    prefix = rules.get("prefix", "")

    if not rules.get("can_analyze", True) and is_analysis:
        return prefix

    if not rules.get("can_conclude", True) and is_analysis:
        return prefix + "\n\n" + answer

    if rules.get("must_warn", False):
        return prefix + "\n\n" + answer if prefix else answer

    return answer


# ---------------------------------------------------------------------------
# 数字防幻觉校验
# ---------------------------------------------------------------------------


def validate_numbers_in_answer(
    *,
    answer: str,
    allowed_numbers: set[float | int],
) -> tuple[bool, list[float | int]]:
    """检查回答中的数字是否全部在允许集合中。

    如果 LLM 编造了业务数字（风险分、ROI、SLA 超时数等），
    这些数字不会出现在 allowed_numbers 中，校验会失败。

    Args:
        answer: LLM 生成的回答文本。
        allowed_numbers: 从工具结果中提取的合法数字集合。

    Returns:
        (is_valid, hallucinated_numbers) — 是否全部合法，以及非法的数字列表。
    """
    # 从回答中提取所有数字
    numbers_in_answer = re.findall(r'\b(\d+(?:\.\d+)?)\b', answer)
    hallucinated = []

    for num_str in numbers_in_answer:
        try:
            num = float(num_str)
            # 跳过纯整数标识符（如 report_id、日期等）
            if num_str.isdigit() and len(num_str) >= 4:
                continue
            if num not in allowed_numbers:
                hallucinated.append(num)
        except ValueError:
            continue

    return len(hallucinated) == 0, hallucinated


def extract_allowed_numbers_from_tool_results(
    tool_results: list[dict[str, Any]],
) -> set[float | int]:
    """从工具结果中提取所有允许的数字。

    递归遍历工具结果数据，提取所有数值类型，作为 LLM 回答中
    数字的合法来源集合。

    Args:
        tool_results: 工具调用结果列表。

    Returns:
        允许的数字集合。
    """
    allowed: set[float | int] = set()

    def _extract(obj: Any) -> None:
        if isinstance(obj, (int, float)):
            allowed.add(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                _extract(v)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _extract(item)

    for result in tool_results:
        _extract(result)

    return allowed


# ---------------------------------------------------------------------------
# 证据占位符系统
# ---------------------------------------------------------------------------


def build_evidence_map(
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """从工具结果构建证据占位符映射。

    每个关键数字分配一个 E{n} 占位符，LLM 在回答中使用占位符引用数字，
    Python 在最终回答中替换为真实值。

    Args:
        tool_results: 所有工具调用的结果数据列表。

    Returns:
        evidence_map: { "E1": 90, "E2": 8, ... }
    """
    evidence_map: dict[str, Any] = {}
    counter = [0]

    def _collect(obj: Any, path: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (int, float)) and k not in (
                    "id", "report_id", "application_id", "student_id",
                    "owner_id", "schema_version", "position", "source_report_id",
                ):
                    counter[0] += 1
                    evidence_map[f"E{counter[0]}"] = v
                elif isinstance(v, (dict, list)):
                    _collect(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, (int, float)) and k not in (
                            "id", "report_id", "application_id", "student_id",
                            "owner_id", "schema_version", "position", "source_report_id",
                        ):
                            counter[0] += 1
                            evidence_map[f"E{counter[0]}"] = v

    for result in tool_results:
        _collect(result)

    return evidence_map
