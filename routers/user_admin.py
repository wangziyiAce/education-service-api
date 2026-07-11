"""管理端用户与角色接口；与登录路由分离，避免重复注册 /auth/login。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schemas import PaginationParams
from schemas.common import success_response
from schemas.student import UserCreate
from services.student_service import create_user, list_roles, list_users
from utils.auth import CurrentUser, get_current_user
from utils.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["用户管理"])

def require_manager(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role_code not in {"admin", "manager"}: raise HTTPException(403, "仅管理员可管理账号")
    return user

@router.get("/users")
def users(page: int = 1, page_size: int = 20, user_type: str | None = None, keyword: str | None = None, status: str | None = None, _: CurrentUser = Depends(require_manager), db: Session = Depends(get_db)):
    return success_response(list_users(db, PaginationParams(page=page, page_size=page_size), user_type, keyword, status))

@router.post("/users")
def create(data: UserCreate, _: CurrentUser = Depends(require_manager), db: Session = Depends(get_db)):
    user = create_user(db, data)
    return success_response({"id": user.id, "username": user.username, "real_name": user.real_name, "user_type": user.user_type, "role_id": user.role_id, "status": user.status})

@router.get("/roles")
def roles(_: CurrentUser = Depends(require_manager), db: Session = Depends(get_db)):
    return success_response({"items": [item.model_dump() for item in list_roles(db)]})
