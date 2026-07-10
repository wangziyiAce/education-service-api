"""智能报告模块 V2 兼容入口。

历史代码和部分路由可能仍然从 ``services.report_service`` 导入函数。
为了不让旧导入路径失效，这里保留一个很薄的兼容层，真正实现已经拆到
``services.reporting`` 包中：

* ``orchestrator``：任务创建、生成、重试；
* ``aggregators``：SQL/规则引擎指标聚合；
* ``registry``：10 类报告注册表；
* ``ai_generator``：Dify 契约与解释生成；
* ``renderer``：后端 HTML 渲染。
"""

from services.reporting.aggregators import aggregate_report as aggregate_report_data
from services.reporting.orchestrator import (
    create_report_task,
    generate_report,
    generate_report_async,
    retry_report,
)

__all__ = [
    "aggregate_report_data",
    "create_report_task",
    "generate_report",
    "generate_report_async",
    "retry_report",
]
