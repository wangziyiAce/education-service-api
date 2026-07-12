"""最小 JWT 鉴权工具。

项目原有 ``models.common`` 里有 JWT 相关代码，但当前本地环境缺少
``python-jose`` 包。为了让报告模块 V2 可以独立导入和演示，这里实现一个
不依赖第三方 JWT 库的 HS256 最小版本。

注意：
----
这不是为了替代成熟安全库。生产项目仍推荐使用 ``python-jose`` 或 PyJWT。
本实现的价值是让课程项目在依赖缺失时也能完成“登录 -> 携带 Token ->
接口识别 generated_by -> RBAC 权限控制”的完整链路训练。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from models.user import SysRole, SysUser
from utils.database import get_db


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """路由层使用的当前登录用户上下文。"""

    id: int
    username: str
    real_name: str
    user_type: str
    role_code: Optional[str]
    department: Optional[str]


def hash_password(password: str) -> str:
    """生成 bcrypt 密码哈希。"""

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """验证明文密码和 bcrypt 哈希是否匹配。"""

    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def create_access_token(user: SysUser, role_code: Optional[str]) -> str:
    """创建 HS256 JWT。

    Payload 里只放身份和权限判断需要的最小信息，不放敏感资料。
    """

    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "user_type": user.user_type,
        "role_code": role_code,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    """验证并解析 JWT。"""

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Token 格式错误") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected, actual):
        raise HTTPException(status_code=401, detail="Token 签名无效")

    payload = json.loads(_b64url_decode(payload_b64))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token 已过期")
    return payload


def get_role_code(db: Session, user: SysUser) -> Optional[str]:
    """根据用户 role_id 查询角色编码；没有角色时退化为 user_type。"""

    if user.role_id:
        role = db.query(SysRole).filter_by(id=user.role_id).first()
        if role:
            return role.role_code
    return user.user_type


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """FastAPI 依赖：从 Authorization 头解析当前用户。"""

    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录，请提供 Bearer Token")
    payload = decode_access_token(credentials.credentials)
    user_id = int(payload["sub"])
    user = db.query(SysUser).filter_by(id=user_id).first()
    if not user or user.status == "disabled":
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return CurrentUser(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        user_type=user.user_type,
        role_code=get_role_code(db, user),
        department=user.department,
    )


def ensure_management_user(user: CurrentUser) -> None:
    """报告模块的管理报告禁止学生访问。"""

    if user.user_type == "student" or user.role_code == "student":
        raise HTTPException(status_code=403, detail="学生角色禁止访问管理报告")


def ensure_report_permission(user: CurrentUser, allowed_roles: tuple[str, ...]) -> None:
    """按报告类型检查角色权限。"""

    ensure_management_user(user)
    if user.role_code == "admin":
        return
    if user.role_code not in allowed_roles:
        raise HTTPException(status_code=403, detail="当前角色无权访问该报告类型")

