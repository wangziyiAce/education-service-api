"""
基础设施模块 — Pydantic Schema
===========================================
用户、角色、组织架构相关的请求/响应数据结构。

包含:
  登录认证:
    LoginRequest        — 登录请求（username + password）
    TokenResponse       — 登录成功返回（Token + 用户信息）
    UserMeResponse      — 当前用户个人信息

  用户管理:
    UserCreate          — 创建用户请求
    UserUpdate          — 更新用户请求
    UserResponse        — 用户信息响应

  角色查询:
    RoleResponse        — 角色信息响应

  组织架构:
    OrganizationCreate  — 创建组织节点请求
    OrganizationResponse — 组织节点响应

⭐ 字段命名严格对齐数据库列名（API 文档第 2.6 节）:
  - real_name（非 display_name / name）
  - user_type（非 role）
  - contact_info（非 phone + email 拆分）
  - create_time（非 created_at）
  - update_time（非 updated_at）
  - org_name（非 name）
  - parent_id（非 parent_org_id）

参考文档:
  《教育服务系统_API接口设计规范文档_V1.2》
  - 第 4.2 节  POST /api/v1/auth/login  — 用户登录
  - 第 4.3 节  GET /api/v1/auth/me     — 当前用户信息
  - 第 2.6 节  字段命名与数据库对齐规范
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 一、登录认证 Schema
# ============================================================

class LoginRequest(BaseModel):
    """
    用户登录请求体。

    对应 API 文档第 4.2 节 POST /api/v1/auth/login。
    前端提交用户名和明文密码，后端用 bcrypt 校验。

    校验规则:
      - username: 必填，1-64 字符
      - password: 必填，1-128 字符（仅做长度校验，不对密码复杂度做强限制）
    """

    username: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="登录账号",
        examples=["admin"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="登录密码（明文，传输时应走 HTTPS）",
        examples=["123456"],
    )


class TokenResponse(BaseModel):
    """
    登录成功后返回的 Token + 用户概要。

    对应 API 文档第 4.2 节 POST /api/v1/auth/login 成功响应 data 部分。
    字段对齐 sys_user 表: user_id, username, real_name, user_type, role_id。
    """

    user_id: int = Field(..., description="用户主键（对应 sys_user.id）")
    username: str = Field(..., description="登录账号")
    real_name: str = Field(..., description="真实姓名（对应 sys_user.real_name）")
    user_type: str = Field(..., description="用户类型（student/employee/admin，对应 sys_user.user_type）")
    role_id: Optional[int] = Field(default=None, description="角色ID（对应 sys_user.role_id）")
    access_token: str = Field(..., description="JWT Token，后续请求放在 Authorization: Bearer {token}")
    token_type: str = Field(default="bearer", description="Token 类型，固定为 bearer")
    expires_in: int = Field(..., description="Token 有效期（秒），默认 86400 = 24小时")


class UserMeResponse(BaseModel):
    """
    当前登录用户的详细信息。

    对应 API 文档第 4.3 节 GET /api/v1/auth/me 成功响应 data 部分。
    字段完全对齐 sys_user 表列名。
    """

    user_id: int = Field(..., description="用户主键")
    username: str = Field(..., description="登录账号")
    real_name: str = Field(..., description="真实姓名")
    user_type: str = Field(..., description="用户类型")
    department: Optional[str] = Field(default=None, description="所属部门/院系")
    contact_info: Optional[str] = Field(default=None, description="联系方式")
    avatar_url: Optional[str] = Field(default=None, description="头像 URL")
    status: str = Field(..., description="账号状态（normal/disabled）")


# ============================================================
# 二、用户管理 Schema
# ============================================================


class UserCreate(BaseModel):
    """
    创建用户请求体。

    字段对齐 sys_user 表必要字段。
    password 接收明文，Service 层用 bcrypt 哈希后存储。
    """

    username: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="登录账号（唯一，不能重复）",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="登录密码（明文，将自动 bcrypt 哈希后入库）",
    )
    real_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="真实姓名",
    )
    user_type: str = Field(
        ...,
        pattern="^(student|employee|admin)$",  # 正则约束：只能是这三个值之一
        description="用户类型: student / employee / admin",
        examples=["employee"],
    )
    role_id: Optional[int] = Field(
        default=None,
        description="角色ID（逻辑关联 sys_role，可为空）",
    )
    department: Optional[str] = Field(
        default=None,
        max_length=128,
        description="所属部门/院系",
    )
    contact_info: Optional[str] = Field(
        default=None,
        max_length=128,
        description="联系方式（手机/邮箱）",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="头像 URL",
    )


class UserUpdate(BaseModel):
    """
    更新用户请求体。

    所有字段均为可选——只传需要修改的字段。
    密码修改应走单独的"修改密码"接口（安全考虑），这里不包含 password 字段。
    """

    real_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="真实姓名",
    )
    user_type: Optional[str] = Field(
        default=None,
        pattern="^(student|employee|admin)$",
        description="用户类型",
    )
    role_id: Optional[int] = Field(
        default=None,
        description="角色ID（逻辑关联 sys_role）",
    )
    department: Optional[str] = Field(
        default=None,
        max_length=128,
        description="所属部门/院系",
    )
    contact_info: Optional[str] = Field(
        default=None,
        max_length=128,
        description="联系方式",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="头像 URL",
    )
    status: Optional[str] = Field(
        default=None,
        pattern="^(normal|disabled)$",
        description="账号状态: normal（正常）/ disabled（禁用）",
    )


class UserResponse(BaseModel):
    """
    用户信息响应体。

    字段严格对齐 sys_user 表所有列名（API 文档第 2.6 节）。
    注意: 不返回 password_hash，密码哈希永远不对外暴露。
    """

    id: int = Field(..., description="主键")
    username: str = Field(..., description="登录账号")
    real_name: str = Field(..., description="真实姓名")
    user_type: str = Field(..., description="用户类型")
    role_id: Optional[int] = Field(default=None, description="角色ID")
    department: Optional[str] = Field(default=None, description="所属部门/院系")
    contact_info: Optional[str] = Field(default=None, description="联系方式")
    avatar_url: Optional[str] = Field(default=None, description="头像 URL")
    status: str = Field(..., description="账号状态")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    # 允许从 ORM 对象直接构造
    model_config = {"from_attributes": True}


# ============================================================
# 三、角色查询 Schema
# ============================================================


class RoleResponse(BaseModel):
    """
    角色信息响应体。

    字段对齐 sys_role 表。
    role_code 是系统内部标识（如 "admin"），role_name 是前端展示名（如 "系统管理员"）。
    """

    id: int = Field(..., description="主键")
    role_code: str = Field(..., description="角色编码（admin/employee/manager/team_leader/student）")
    role_name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(default=None, description="角色描述")
    status: int = Field(..., description="状态: 1=启用 0=禁用")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


# ============================================================
# 四、组织架构 Schema
# ============================================================


class OrganizationCreate(BaseModel):
    """
    创建组织节点请求体。

    字段对齐 sys_organization 表。
    parent_id 为 None 表示根组织（树的顶层节点），非 None 表示某个组织的子节点。
    """

    org_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="组织名称",
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="上级组织ID（逻辑关联 sys_organization，NULL=根节点）",
    )
    org_type: Optional[str] = Field(
        default=None,
        max_length=32,
        description="组织类型（如 company/department/team）",
    )
    sort_order: int = Field(
        default=0,
        description="同级排序权重（数值越小越靠前）",
    )


class OrganizationResponse(BaseModel):
    """
    组织节点响应体。

    字段对齐 sys_organization 表。
    children 字段用于返回树形结构（递归嵌套），仅在查询组织树时填充。
    """

    id: int = Field(..., description="主键")
    org_name: str = Field(..., description="组织名称")
    parent_id: Optional[int] = Field(default=None, description="上级组织ID")
    org_type: Optional[str] = Field(default=None, description="组织类型")
    sort_order: int = Field(..., description="排序权重")
    status: int = Field(..., description="状态: 1=启用 0=禁用")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    children: list["OrganizationResponse"] = Field(
        default_factory=list,
        description="子组织列表（树形结构，递归）",
    )

    model_config = {"from_attributes": True}


# ============================================================
# 五、密码修改 Schema
# ============================================================


class PasswordChangeRequest(BaseModel):
    """
    修改密码请求体。

    要求输入旧密码验证身份，新密码最少 6 位。
    """

    old_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="当前密码（用于身份验证）",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="新密码（最少 6 位）",
    )
