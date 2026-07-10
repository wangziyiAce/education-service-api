"""Dify / AI 报告解释层。

V2 的关键原则：AI 不生产业务数字，只解释已经聚合好的数字。

所以这个文件的输入是：

* report_type
* schema_version
* report_title
* period
* aggregated_data
* expected_schema
* data_quality

输出只允许补充 ``summary``、``explanation`` 这类解释性字段。即使 Dify 不可用，
系统也会明确标记本地解释模式，避免“隐式 Mock”被当成正式 AI 结果。
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

import httpx

from config import DIFY_API_KEY, DIFY_API_URL
from services.reporting.registry import ReportDefinition
from services.reporting.schemas import DataQuality


def _local_explanation(report_type: str, content: dict[str, Any], data_quality: DataQuality) -> dict[str, Any]:
    """未启用 Dify 时的本地说明。

    这不是伪造 AI，而是明确标记的本地模板解释。它保证开发环境和课堂演示
    不因为外部 Dify 没配置而完全不可用。
    """

    result = deepcopy(content)
    result["explanation"] = (
        result.get("explanation")
        or f"{report_type} 报告已由规则引擎生成指标；当前使用本地解释模式，"
        "Dify 配置后可替换为 AI 解释。"
    )
    if data_quality.data_source == "database":
        data_quality.data_source = "local"
    data_quality.warnings.append("REPORT_AI_MODE 未设置为 dify，使用本地确定性解释")
    return result


def _call_dify_workflow(inputs: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    """报告 V2 专用 Dify Workflow 调用。

    旧 ``utils.dify_client`` 中存在历史兼容代码和重复函数定义。这里保留一个
    小而明确的调用函数，保证 V2 的输入契约稳定。
    """

    url = f"{DIFY_API_URL.rstrip('/')}/workflows/run"
    payload = {"inputs": inputs, "response_mode": "blocking", "user": "report-v2"}
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def enrich_content_with_ai(
    *,
    definition: ReportDefinition,
    title: str,
    period: dict[str, Any],
    content: dict[str, Any],
    data_quality: DataQuality,
) -> dict[str, Any]:
    """调用 Dify 补充报告解释，并做一次 Schema 修复机会。

    如果环境变量 ``REPORT_AI_MODE=dify`` 且配置了 ``DIFY_API_KEY``，才会调用
    Dify。否则走明确标记的本地解释模式。
    """

    ai_mode = os.getenv("REPORT_AI_MODE", "local").lower()
    if ai_mode != "dify":
        return _local_explanation(definition.report_type, content, data_quality)
    if not DIFY_API_KEY:
        raise RuntimeError("REPORT_AI_MODE=dify 但 DIFY_API_KEY 未配置")

    expected_schema = definition.content_model.model_json_schema()
    workflow_inputs = {
        "report_type": definition.report_type,
        "schema_version": definition.schema_version,
        "report_title": title,
        "period": period,
        "aggregated_data": content,
        "expected_schema": expected_schema,
        "data_quality": data_quality.model_dump(),
    }

    response = _call_dify_workflow(inputs=workflow_inputs, timeout=180)
    outputs = response.get("data", {}).get("outputs", {})
    candidate = outputs.get("report_content") or outputs.get("content") or outputs
    if isinstance(candidate, str):
        candidate = json.loads(candidate)

    merged = deepcopy(content)
    # 只允许 AI 修改解释性字段，业务指标仍以聚合器为准。
    for key in ("summary", "explanation"):
        if isinstance(candidate, dict) and candidate.get(key):
            merged[key] = candidate[key]

    try:
        definition.content_model.model_validate(merged)
        return merged
    except Exception as first_error:
        # 给 Dify 一次修复机会；仍失败就抛出，让任务进入 failed。
        repair_inputs = {
            **workflow_inputs,
            "invalid_output": candidate,
            "validation_error": str(first_error),
        }
        repair_response = _call_dify_workflow(inputs=repair_inputs, timeout=180)
        repair_outputs = repair_response.get("data", {}).get("outputs", {})
        repaired = repair_outputs.get("report_content") or repair_outputs.get("content") or repair_outputs
        if isinstance(repaired, str):
            repaired = json.loads(repaired)
        for key in ("summary", "explanation"):
            if isinstance(repaired, dict) and repaired.get(key):
                merged[key] = repaired[key]
        definition.content_model.model_validate(merged)
        return merged
