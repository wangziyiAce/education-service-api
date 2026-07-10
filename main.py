"""教育服务系统 - FastAPI 应用入口。

本文件负责三件事：

1. 创建 FastAPI 应用；
2. 在应用启动时尝试初始化数据库表；
3. 注册各业务模块路由。

本轮智能报告 V2 已接入：

* ``/api/v1/auth``：最小 JWT 登录；
* ``/api/v1/reports``：报告生成、查询、重试、类型、报告内行动项；
* ``/api/v1/report-schedules``：定时报告计划 CRUD；
* ``/api/v1/report-actions``：行动项独立查询/更新；
* ``/api/v1/report-data``：报告事实数据维护；
* ``/api/v1/crm`` 与 ``/api/v1/student``：状态联动接口。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import APP_DEBUG, APP_NAME, APP_VERSION
from utils.database import init_db


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。

    课程项目常见情况是：有些同学本地还没启动 MySQL，但仍希望能打开 Swagger
    查看接口契约。因此这里会尝试初始化数据库；如果失败，记录错误但不阻止
    应用启动。真正调用需要数据库的接口时仍会返回数据库连接错误。
    """

    try:
        init_db()
    except Exception as exc:  # pragma: no cover - 依赖本地 MySQL 环境
        logger.warning("数据库初始化失败，应用继续启动以便查看接口文档：%s", exc)
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=APP_DEBUG,
    lifespan=lifespan,
)


@app.get("/health", tags=["系统"])
def health_check() -> dict:
    """服务健康检查。"""

    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


# 路由注册集中放在入口文件，方便 Swagger 一眼看到系统模块。
from routers import auth, crm, report, report_action, report_data, report_schedule, student  # noqa: E402

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(report.router, prefix="/api/v1/reports", tags=["智能报告"])
app.include_router(report_schedule.router, prefix="/api/v1/report-schedules", tags=["报告调度"])
app.include_router(report_action.router, prefix="/api/v1/report-actions", tags=["报告行动项"])
app.include_router(report_data.router, prefix="/api/v1/report-data", tags=["报告事实数据"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["CRM联动"])
app.include_router(student.router, prefix="/api/v1/student", tags=["学生服务联动"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
