"""报告 HTML 渲染器。

V1 里常见的做法是让大模型直接输出 HTML，这样有两个问题：

1. 安全风险：模型可能输出不可控脚本或破坏页面结构；
2. 前端体验不可控：不同报告样式不一致，难以维护。

V2 改为：后端按报告类型选择模板，模型只输出结构化 JSON 和解释文本。
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from services.reporting.registry import ReportDefinition


def _safe_json(data: Any) -> str:
    """把复杂指标转成可读 JSON，并做 HTML 转义。"""

    return html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def render_report_html(
    *,
    definition: ReportDefinition,
    title: str,
    period: dict[str, Any],
    content: dict[str, Any],
    data_quality: dict[str, Any],
) -> str:
    """渲染报告 HTML。

    当前实现使用轻量内置模板，模板名仍来自注册表，方便后续替换为 Jinja2
    的独立模板文件。这里不引入复杂前端依赖，保证课程项目可运行。
    """

    escaped_title = html.escape(title)
    summary = html.escape(str(content.get("summary", "")))
    explanation = html.escape(str(content.get("explanation", "")))
    period_text = html.escape(f"{period.get('start')} ~ {period.get('end')}")
    metrics = content.get("metrics") or content.get("sla_overview") or content.get("channel_metrics") or {}
    content_json = _safe_json(content)
    data_quality_json = _safe_json(data_quality)

    template_path = Path("templates") / "reports" / definition.template_name
    if template_path.exists():
        # 这里使用轻量字符串替换而不是直接引入模板引擎，避免课堂环境依赖过重。
        # 如果后续升级 Jinja2，模板文件可以基本原样复用。
        template = template_path.read_text(encoding="utf-8")
        return (
            template.replace("{{ title }}", escaped_title)
            .replace("{{ report_label }}", html.escape(definition.label))
            .replace("{{ period }}", period_text)
            .replace("{{ summary }}", summary)
            .replace("{{ explanation }}", explanation)
            .replace("{{ metrics_json }}", _safe_json(metrics))
            .replace("{{ content_json }}", content_json)
            .replace("{{ data_quality_json }}", data_quality_json)
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{escaped_title}</title>
  <style>
    body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }}
    main {{ max-width: 960px; margin: 32px auto; background: white; padding: 32px; border-radius: 16px; box-shadow: 0 8px 24px rgba(15, 23, 42, .08); }}
    h1 {{ margin: 0 0 8px; color: #0f172a; }}
    h2 {{ margin-top: 28px; color: #1d4ed8; }}
    .meta {{ color: #64748b; margin-bottom: 20px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; }}
    .quality {{ color: #92400e; background: #fffbeb; border-color: #fde68a; }}
  </style>
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    <div class="meta">类型：{html.escape(definition.label)} ｜ 周期：{period_text} ｜ 模板：{html.escape(definition.template_name)}</div>
    <h2>报告摘要</h2>
    <div class="card">{summary}</div>
    <h2>核心指标</h2>
    <div class="card"><pre>{_safe_json(metrics)}</pre></div>
    <h2>解释说明</h2>
    <div class="card">{explanation}</div>
    <h2>数据质量</h2>
    <div class="card quality"><pre>{data_quality_json}</pre></div>
  </main>
</body>
</html>"""
