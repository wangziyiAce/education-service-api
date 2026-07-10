"""数据库连接与初始化。

这个文件是 FastAPI 与 MySQL 的公共入口：

* ``engine``：数据库连接池；
* ``SessionLocal``：数据库会话工厂；
* ``Base``：所有 SQLAlchemy ORM 模型的基类；
* ``get_db``：FastAPI 依赖注入，每个请求自动获取/关闭 Session；
* ``init_db``：应用启动时注册模型、建表、写入最小种子数据。

为什么本轮重写？
----------------
旧版本的 ``init_db`` 依赖 ``services.student_service``，而该文件又依赖当前环境
未安装的 ``python-jose``。报告 V2 需要稳定地注册新表，所以这里把初始化逻辑
收敛到数据库工具层本身，减少不必要的启动耦合。
"""

from __future__ import annotations

from typing import Generator

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

from config import (
    DATABASE_URL,
    DB_ECHO,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
)


engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=DB_ECHO,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供一个数据库 Session。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _hash_seed_password(password: str) -> str:
    """种子用户密码哈希。

    这里不从 ``utils.auth`` 导入，避免数据库层和认证层循环依赖。
    """

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_basic_users(db: Session) -> None:
    """写入最小角色和管理员账号。

    种子数据只在表为空或用户不存在时写入，重复启动不会重复插入。
    """

    from models.user import SysRole, SysUser

    if db.query(SysRole).count() == 0:
        db.add_all(
            [
                SysRole(role_code="admin", role_name="系统管理员", description="拥有全部管理权限"),
                SysRole(role_code="manager", role_name="部门经理", description="查看部门管理报告"),
                SysRole(role_code="employee", role_name="员工/顾问", description="查看本人负责数据"),
                SysRole(role_code="team_leader", role_name="班主任", description="查看授权学生服务数据"),
                SysRole(role_code="student", role_name="学生", description="学生端角色，禁止管理报告"),
            ]
        )
        db.commit()

    if db.query(SysUser).filter_by(username="admin").count() == 0:
        admin_role = db.query(SysRole).filter_by(role_code="admin").first()
        admin = SysUser(
            username="admin",
            password_hash=_hash_seed_password("admin123"),
            real_name="系统管理员",
            user_type="admin",
            role_id=admin_role.id if admin_role else None,
            department="技术部",
            contact_info="admin@example.com",
            status="normal",
        )
        db.add(admin)
        db.commit()


def init_db() -> None:
    """注册全部 ORM 模型并创建表。

    ``create_all`` 只会创建不存在的表，不会自动 ALTER 已有表。生产环境仍建议
    使用 Alembic 或显式 SQL 迁移；本项目同步提供了 ``db_init.sql``。
    """

    import models.crm  # noqa: F401
    import models.report  # noqa: F401
    import models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_basic_users(db)
    finally:
        db.close()
