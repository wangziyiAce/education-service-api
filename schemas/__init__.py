"""
教育服务系统 — 通用 Pydantic Schema
===========================================
所有 API 接口共用的请求/响应数据结构定义在这里。

包含:
  - ApiResponse         统一响应泛型模型
  - PaginationParams    通用分页请求参数
  - PaginatedResponse   分页响应格式

为什么放在 schemas/__init__.py 而不是单独文件？
  这些是"元 Schema"——不归属任何业务模块，是所有模块的共同语言。
  放在 __init__.py 里，外部可以直接 from schemas import ApiResponse，
  与 Pydantic 的 BaseModel 一样的 import 体验。

字段命名对齐:
  JSON 字段名严格使用 snake_case，与数据库列名一一对应。
  见 API 文档第 2.6 节：字段命名与数据库对齐规范。

参考文档:
  《教育服务系统_API接口设计规范文档_V1.2》
  - 第 2.3 节  统一响应格式
  - 第 12.1 节 分页参数标准化
  - 第 2.5 节  Pydantic Schema 命名规范
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# ============================================================
# 泛型类型变量
# ============================================================
# TypeVar 让 ApiResponse 和 PaginatedResponse 可以与任何数据类型组合:
#   ApiResponse[UserResponse]     → data 字段类型是 UserResponse
#   PaginatedResponse[UserResponse] → items 字段类型是 List[UserResponse]

T = TypeVar("T")  # 代表任意 Pydantic Model 或 dict


# ============================================================
# ApiResponse — 统一响应模型
# ============================================================
# 对应 API 文档第 2.3 节统一响应格式。
#
# 使用方式:
#   # 在路由中返回 Pydantic Model 时用 response_model 指定
#   @router.get("/users", response_model=ApiResponse[PaginatedResponse[UserResponse]])
#
#   # 在 Service 层手动构造 dict 时用 success_response() / error_response()
#   return success_response(data=user_dict)
#
# 两者效果相同，最终返回给前端的 JSON 格式都是:
#   {"code": 0, "message": "success", "data": {...}}
# ============================================================


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应泛型模型。

    泛型参数 T 指定 data 字段的类型。
    可以直接用这个返回，也可以手动构造 dict（多数场景用 success_response() 更方便）。
    """

    code: int = Field(default=0, description="业务状态码，0=成功，非0=错误（见 API 文档第 3 章）")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="响应数据体")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": 0,
                "message": "success",
                "data": {"id": 1, "username": "admin"},
            }
        }
    }


# ============================================================
# PaginationParams — 通用分页请求参数
# ============================================================
# 对应 API 文档第 12.1 节分页参数标准化。
#
# 所有列表查询接口统一使用这两个参数，不需要每个接口重复定义。
# 前端传参示例:
#   GET /api/v1/auth/users?page=1&page_size=20
#
# 使用方式:
#   @router.get("/users")
#   def list_users(
#       pagination: PaginationParams = Depends(),
#       db: Session = Depends(get_db),
#   ):
#       users = db.query(SysUser).offset(pagination.skip).limit(pagination.limit).all()
# ============================================================


class PaginationParams(BaseModel):
    """
    通用分页请求参数。

    作为 FastAPI 依赖使用时: PaginationParams = Depends()
    FastAPI 会自动从查询字符串 ?page=1&page_size=20 中取值并校验。
    """

    page: int = Field(
        default=1,
        ge=1,  # greater than or equal to 1
        description="页码，从 1 开始",
    )
    page_size: int = Field(
        default=20,
        ge=1,   # 最少 1 条
        le=100, # 最多 100 条（防止一次查询过多拖垮数据库）
        description="每页条数，最大 100",
    )

    @property
    def skip(self) -> int:
        """
        SQL OFFSET 的值。

        计算方式: (page - 1) * page_size
        示例: page=3, page_size=20 → skip=40（跳过前 40 条，返回第 41-60 条）
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQL LIMIT 的值，与 page_size 相同（已在上限内约束）。"""
        return self.page_size


# ============================================================
# PaginatedResponse — 分页响应格式
# ============================================================
# 对应 API 文档第 2.3 节列表+分页响应格式。
#
# 返回的 JSON 格式:
#   {
#     "items": [...],
#     "total": 100,
#     "page": 1,
#     "page_size": 20
#   }
# ============================================================


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页列表响应模型。

    泛型参数 T 指定 items 列表中每个元素的类型。
    """

    items: List[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(default=0, description="符合条件的总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
            }
        }
    }
