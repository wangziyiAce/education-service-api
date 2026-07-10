"""认证接口 Schema。

本项目只实现最小 JWT 登录能力，目标是让报告生成、查询和调度接口能拿到
``generated_by``，并按角色做管理报告访问控制。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="登录账号")
    password: str = Field(..., description="明文密码，仅用于登录请求，不入库")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    real_name: str
    user_type: str
    role_code: Optional[str] = None


class CurrentUserResponse(BaseModel):
    user_id: int
    username: str
    real_name: str
    user_type: str
    role_code: Optional[str] = None
    department: Optional[str] = None

