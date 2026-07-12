"""最小 JWT 认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import SysUser
from schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from utils.auth import (
    CurrentUser,
    create_access_token,
    get_current_user,
    get_role_code,
    verify_password,
)
from utils.database import get_db


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """用户登录。

    登录成功后返回 Bearer Token；后续报告接口用该 Token 识别 generated_by。
    """

    user = db.query(SysUser).filter_by(username=request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status == "disabled":
        raise HTTPException(status_code=401, detail="账号已禁用")

    role_code = get_role_code(db, user)
    token = create_access_token(user, role_code)
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        user_type=user.user_type,
        role_code=role_code,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    """获取当前登录用户信息。"""

    return CurrentUserResponse(
        user_id=current_user.id,
        username=current_user.username,
        real_name=current_user.real_name,
        user_type=current_user.user_type,
        role_code=current_user.role_code,
        department=current_user.department,
    )

