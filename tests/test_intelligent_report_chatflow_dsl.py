"""智能报告 Chatflow DSL 的静态契约测试。

测试层职责：读取最终交付的 Dify YAML，并验证它没有偏离后端已经固定的 Chatflow
契约。这里不调用真实大模型，避免把 API Key、模型余额和网络状态混进结构测试。

上游是 ``doc/智能报告Chatflow设计.md`` 与报告 V2 后端契约；下游是 Dify 1.14.2
导入器。断言失败时应先看测试报告指出的节点、边或变量，再到 DSL 中定位相同 ID。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DSL_PATH = PROJECT_ROOT / "doc" / "智能报告模块V2_Chatflow_Dify1.14.2.yml"

DEEPSEEK_PROVIDER = "langgenius/deepseek/deepseek"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_DEPENDENCY = (
    "langgenius/deepseek:0.0.19@"
    "5b68617c637b62d31e7f33a9f5677b76e88f81868fb04a728e208588564b72ea"
)

SUPPORTED_REPORT_TYPES = {
    "customer_ops",
    "daily_summary",
    "weekly_summary",
    "psych_weekly",
    "complaint_weekly",
    "application_risk",
    "sales_funnel",
    "channel_roi",
    "service_sla",
    "action_closure",
}

START_VARIABLE_TYPES = {
    "report_type": "text-input",
    "schema_version": "number",
    "report_title": "text-input",
    "period": "json_object",
    "aggregated_data": "json_object",
    "expected_schema": "json_object",
    "data_quality": "json_object",
    "invalid_output": "json_object",
    "validation_error": "paragraph",
}


def _load_dsl() -> dict[str, Any]:
    """读取真实交付文件，确保测试验证的是用户最终会导入 Dify 的产物。"""

    assert DSL_PATH.exists(), f"目标 DSL 尚未生成: {DSL_PATH}"
    with DSL_PATH.open("r", encoding="utf-8") as file:
        document = yaml.safe_load(file)
    assert isinstance(document, dict), "DSL 顶层必须是 YAML 对象"
    return document


def _graph(document: dict[str, Any]) -> dict[str, Any]:
    """取得 Dify graph；集中访问可让后续断言错误更容易定位。"""

    graph = document["workflow"]["graph"]
    assert isinstance(graph, dict)
    return graph


def _nodes_by_id(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按唯一节点 ID 建立索引，并用长度比较同时发现重复 ID。"""

    nodes = _graph(document)["nodes"]
    indexed = {node["id"]: node for node in nodes}
    assert len(indexed) == len(nodes), "节点 ID 必须唯一"
    return indexed


def test_dsl_has_dify_1142_top_level_contract_and_dependency() -> None:
    """验证目标版本、应用模式和 DeepSeek 插件依赖可以被导入器识别。"""

    document = _load_dsl()

    assert document["kind"] == "app"
    assert document["version"] == "0.6.0"
    assert document["app"]["mode"] == "advanced-chat"
    dependency_text = str(document["dependencies"])
    assert DEEPSEEK_DEPENDENCY in dependency_text
    assert document["workflow"]["conversation_variables"] == []
    assert document["workflow"]["environment_variables"] == []
    assert document["workflow"]["rag_pipeline_variables"] == []


def test_graph_has_15_nodes_14_edges_and_consistent_references() -> None:
    """验证设计规定的最小图规模，并避免边或 selector 指向不存在的节点。"""

    document = _load_dsl()
    graph = _graph(document)
    nodes = _nodes_by_id(document)

    assert len(nodes) == 15
    assert len(graph["edges"]) == 14
    for edge in graph["edges"]:
        assert edge["source"] in nodes
        assert edge["target"] in nodes

    for node in nodes.values():
        for variable in node.get("data", {}).get("variables", []):
            selector = variable.get("value_selector")
            if selector:
                assert selector[0] in nodes, f"selector 指向未知节点: {selector}"


def test_start_defines_exact_nine_inputs_with_json_objects() -> None:
    """验证后端 ``inputs`` 的九个字段与 Dify Start 变量类型完全一致。"""

    document = _load_dsl()
    start_nodes = [node for node in _graph(document)["nodes"] if node["data"]["type"] == "start"]

    assert len(start_nodes) == 1
    variables = {item["variable"]: item["type"] for item in start_nodes[0]["data"]["variables"]}
    assert variables == START_VARIABLE_TYPES


def test_code_node_validates_all_inputs_routes_ten_types_and_builds_context_json() -> None:
    """验证 Code 节点承担输入校验和路由，不把业务指标计算交给模型。"""

    document = _load_dsl()
    code_nodes = [node for node in _graph(document)["nodes"] if node["data"]["type"] == "code"]

    assert len(code_nodes) == 1
    code_node = code_nodes[0]
    bound_names = {item["variable"] for item in code_node["data"]["variables"]}
    assert bound_names == set(START_VARIABLE_TYPES)
    assert set(code_node["data"]["outputs"]) == {
        "is_valid",
        "error_code",
        "error_message",
        "report_group",
        "report_focus",
        "privacy_rules_text",
        "is_empty_data",
        "is_repair_mode",
        "context_json",
    }

    code = code_node["data"]["code"]
    for report_type in SUPPORTED_REPORT_TYPES:
        assert f'"{report_type}"' in code
    assert "invalid_output" in code
    assert "validation_error" in code
    assert "context_json" in code
    assert "psych_weekly" in code
    assert "心理咨询原文" in code


def test_two_if_else_nodes_route_all_groups_and_invalid_input() -> None:
    """验证一个条件负责合法性、另一个条件负责五组报告路由。"""

    document = _load_dsl()
    if_nodes = [node for node in _graph(document)["nodes"] if node["data"]["type"] == "if-else"]
    cases = [case for node in if_nodes for case in node["data"]["cases"]]
    case_text = str(cases)

    assert len(if_nodes) == 2
    assert "is_valid" in case_text
    for group in ("application_risk", "sales_funnel", "channel_roi", "service_privacy", "management"):
        assert group in case_text


def test_five_llms_use_deepseek_and_each_connects_directly_to_own_answer() -> None:
    """验证五个解释分支不经过共享 normalize，防止异常输出被伪装为成功。"""

    document = _load_dsl()
    graph = _graph(document)
    nodes = _nodes_by_id(document)
    llms = [node for node in nodes.values() if node["data"]["type"] == "llm"]

    assert len(llms) == 5
    for llm in llms:
        model = llm["data"]["model"]
        assert model["provider"] == DEEPSEEK_PROVIDER
        assert model["name"] == DEEPSEEK_MODEL
        outgoing = [edge for edge in graph["edges"] if edge["source"] == llm["id"]]
        assert len(outgoing) == 1
        assert nodes[outgoing[0]["target"]]["data"]["type"] == "answer"
        answer = nodes[outgoing[0]["target"]]["data"]["answer"]
        assert f"{{{{#{llm['id']}.text#}}}}" in answer


def test_prompts_protect_numbers_privacy_and_repair_context() -> None:
    """验证每个模型都真正读取修复上下文，并遵守数字与心理隐私边界。"""

    document = _load_dsl()
    llms = [node for node in _graph(document)["nodes"] if node["data"]["type"] == "llm"]

    for llm in llms:
        prompt_text = str(llm["data"]["prompt_template"])
        assert "context_json" in prompt_text
        assert "invalid_output" in prompt_text
        assert "validation_error" in prompt_text
        assert "summary" in prompt_text and "explanation" in prompt_text
        assert "不改写" in prompt_text or "禁止改写" in prompt_text

    all_prompts = "\n".join(str(llm["data"]["prompt_template"]) for llm in llms)
    assert "心理咨询原文" in all_prompts
    assert "诊断" in all_prompts
    assert "可识别" in all_prompts


def test_invalid_answer_is_non_json_sentinel_and_dsl_has_no_placeholders() -> None:
    """验证非法输入显式失败，并禁止 normalize 或设计阶段占位符混入交付物。"""

    document = _load_dsl()
    raw_text = DSL_PATH.read_text(encoding="utf-8")
    answers = [node for node in _graph(document)["nodes"] if node["data"]["type"] == "answer"]
    invalid_answers = [node for node in answers if "CHATFLOW_ERROR|" in node["data"]["answer"]]

    assert len(answers) == 6
    assert len(invalid_answers) == 1
    sentinel = invalid_answers[0]["data"]["answer"]
    assert "{" not in sentinel and "}" not in sentinel
    # ``normalized_version`` 是普通局部变量，不是被禁止的清洗节点；因此节点禁用规则
    # 必须检查 graph 元数据，不能对整个代码文本做会产生误报的子串搜索。
    node_metadata = "\n".join(
        f"{node['id']} {node['data'].get('title', '')} {node['data'].get('type', '')}"
        for node in _graph(document)["nodes"]
    ).lower()
    assert "normalize" not in node_metadata
    for forbidden in ("TODO", "TBD", "N02", "上游LLM节点输出"):
        assert forbidden not in raw_text


def test_every_node_has_detailed_chinese_description() -> None:
    """验证教学项目的节点注释可说明责任、数据去向和排错入口。"""

    document = _load_dsl()

    for node in _graph(document)["nodes"]:
        description = node["data"].get("desc", "")
        assert len(description) >= 35, f"节点 {node['id']} 的中文说明过短"
        assert any(keyword in description for keyword in ("输入", "上游", "接收"))
        assert any(keyword in description for keyword in ("输出", "下游", "返回"))
        assert any(keyword in description for keyword in ("排查", "错误", "失败", "检查"))
