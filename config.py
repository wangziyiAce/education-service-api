"""项目统一运行配置。

本模块位于公共配置层：FastAPI 入口、数据库连接、认证、Dify 客户端和测试都从
这里读取运行参数。配置来源按“进程环境变量优先、项目根目录 .env 兜底”的顺序
处理，避免每个业务模块自行读取环境变量而产生不一致。

对外同时保留 ``settings`` 对象和历史模块级常量。前者供新代码统一使用，后者
保证 ``from config import DATABASE_URL`` 等已有导入路径继续可用。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


# 只从项目根目录加载本地开发配置；override=False 确保部署平台注入的环境变量优先。
load_dotenv(Path(__file__).with_name(".env"), override=False)


def _read_int(name: str, default: int) -> int:
    """读取整数配置；空值回退默认值，非法值给出可定位的配置错误。"""

    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是整数，当前值无法转换") from exc


def _read_bool(name: str, default: bool) -> bool:
    """读取布尔配置，避免字符串 'false' 在 Python 中被误判为真。"""

    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _first_non_empty(*names: str, default: str = "") -> str:
    """按名称顺序返回第一个非空环境变量，用于新旧命名兼容。"""

    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    """应用运行配置对象。

    数据从环境变量或 ``.env`` 读取。``DATABASE_URL`` 是数据库连接的唯一优先
    入口；仅当它未提供时，才使用历史 DB_* 字段拼接 MySQL URL，便于旧部署平滑
    迁移。数据库、认证和 Dify 的敏感值不会在这里记录或打印。
    """

    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    APP_DEBUG: bool
    DATABASE_URL: str
    DB_ECHO: bool
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int
    DB_POOL_TIMEOUT: int
    DB_POOL_RECYCLE: int
    SECRET_KEY: str
    BCRYPT_COST: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    DIFY_API_URL: str
    DIFY_API_KEY: str
    DIFY_SERVICE_TOKEN: str

    @property
    def is_development(self) -> bool:
        """仅 development 环境允许应用启动时创建缺失表和写入幂等种子数据。"""

        return self.APP_ENV.lower() == "development"

    @classmethod
    def from_environment(cls) -> "Settings":
        """把环境变量转换为统一配置，并保留旧变量命名的兼容入口。"""

        db_host = _first_non_empty("DB_HOST", default="localhost")
        db_port = _read_int("DB_PORT", 3306)
        db_user = _first_non_empty("DB_USER")
        db_password = _first_non_empty("DB_PASSWORD")
        db_name = _first_non_empty("DB_NAME")
        db_charset = _first_non_empty("DB_CHARSET", default="utf8mb4")

        database_url = _first_non_empty("DATABASE_URL")
        if not database_url and db_user and db_name:
            # 对密码做 URL 编码，避免 @、: 等字符破坏 SQLAlchemy 连接字符串。
            database_url = (
                f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}"
                f"@{db_host}:{db_port}/{db_name}?charset={db_charset}"
            )

        access_token_minutes = _read_int("ACCESS_TOKEN_EXPIRE_MINUTES", 0)
        if access_token_minutes <= 0:
            access_token_minutes = _read_int("JWT_EXPIRE_HOURS", 24) * 60

        return cls(
            APP_NAME=_first_non_empty("APP_NAME", default="教育服务系统 API"),
            APP_VERSION=_first_non_empty("APP_VERSION", default="1.0.0"),
            APP_ENV=_first_non_empty("APP_ENV", default="production"),
            APP_DEBUG=_read_bool("APP_DEBUG", False),
            DATABASE_URL=database_url,
            DB_ECHO=_read_bool("DB_ECHO", False),
            DB_POOL_SIZE=_read_int("DB_POOL_SIZE", 10),
            DB_MAX_OVERFLOW=_read_int("DB_MAX_OVERFLOW", 20),
            DB_POOL_TIMEOUT=_read_int("DB_POOL_TIMEOUT", 30),
            DB_POOL_RECYCLE=_read_int("DB_POOL_RECYCLE", 3600),
            SECRET_KEY=_first_non_empty("JWT_SECRET_KEY", "SECRET_KEY"),
            BCRYPT_COST=_read_int("BCRYPT_COST", 12),
            ACCESS_TOKEN_EXPIRE_MINUTES=access_token_minutes,
            DIFY_API_URL=_first_non_empty(
                "DIFY_API_BASE_URL",
                "DIFY_API_URL",
                default="http://localhost:5001/v1",
            ),
            DIFY_API_KEY=_first_non_empty("DIFY_API_KEY"),
            DIFY_SERVICE_TOKEN=_first_non_empty("DIFY_SERVICE_TOKEN"),
        )


# 新代码使用 settings；下方别名保证存量模块不需要同步改写导入方式。
settings = Settings.from_environment()

APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
APP_ENV = settings.APP_ENV
APP_DEBUG = settings.APP_DEBUG
DATABASE_URL = settings.DATABASE_URL
DB_ECHO = settings.DB_ECHO
DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
DB_POOL_TIMEOUT = settings.DB_POOL_TIMEOUT
DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE
SECRET_KEY = settings.SECRET_KEY
BCRYPT_COST = settings.BCRYPT_COST
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
DIFY_API_URL = settings.DIFY_API_URL
DIFY_API_KEY = settings.DIFY_API_KEY
DIFY_SERVICE_TOKEN = settings.DIFY_SERVICE_TOKEN
