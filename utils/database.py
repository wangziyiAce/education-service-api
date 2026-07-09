"""
数据库连接工具
负责：创建 SQLAlchemy 引擎、Session 工厂、get_db 依赖
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# 从配置文件读取数据库 URL（开发阶段可直接写死）
try:
    from config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    # 默认配置，可被 .env 文件覆盖
    import os
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/education_service"
    )

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,         # 连接池健康检查
    pool_size=10,               # 连接池大小
    max_overflow=20,            # 最大溢出连接数
    echo=False,                 # 是否打印 SQL（调试时设为 True）
)

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_session() -> Session:
    """手动创建 Session（用于定时任务等非依赖注入场景）"""
    return SessionLocal()
