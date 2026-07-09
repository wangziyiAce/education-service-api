"""
基础设施模块 — 用户/角色/组织 业务服务层
===========================================
所有基础设施相关的业务逻辑在这里实现。

核心职责:
  1. 用户认证      — 登录验证（bcrypt 密码校验 + JWT 签发）
  2. 用户管理      — CRUD（创建/查询/更新，含逻辑外键校验）
  3. 角色查询      — 角色列表（用于前端下拉菜单、权限判断）
  4. 组织架构管理  — 组织树查询 + 创建节点

无物理外键策略（对应 API 文档第 14 章）:
  - 创建用户时: 如果传了 role_id，必须校验 sys_role 中存在该角色
  - 创建组织时: 如果传了 parent_id，必须校验 sys_organization 中存在父节点
  - 所有校验在 Service 层完成，数据库层面不做 FOREIGN KEY 约束

事务边界（对应 API 文档第 14.5 节）:
  - 写操作使用 with db.begin() 确保原子性
  - 事务内不调用外部 API（Dify、邮件等）

参考文档:
  《教育服务系统_API接口设计规范文档_V1.2》
  - 第 4 章   认证与鉴权接口
  - 第 14 章  应用层数据一致性保障
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# --- 公共基础 ---
from models.common import (
    AuthError,
    ConflictError,
    NotFoundError,
    ReferenceNotFoundError,
    ValidationError,
    create_access_token,
    hash_password,
    verify_password,
)

# --- 数据模型 ---
from models.user import SysOrganization, SysRole, SysUser

# --- Schema ---
from schemas import PaginationParams
from schemas.student import (
    OrganizationCreate,
    OrganizationResponse,
    RoleResponse,
    TokenResponse,
    UserCreate,
    UserMeResponse,
    UserResponse,
    UserUpdate,
)


# ============================================================
# 一、用户认证
# ============================================================

def authenticate_user(db: Session, username: str, password: str) -> TokenResponse:
    """
    验证用户登录并签发 JWT Token。

    对应 API 文档第 4.2 节 POST /api/v1/auth/login。

    流程:
      1. 按 username 查 sys_user 表
      2. bcrypt 校验密码
      3. 检查账号状态（disabled 不允许登录）
      4. 签发 JWT Token 并返回用户信息

    参数:
        db:       数据库会话
        username: 登录账号
        password: 明文密码

    返回:
        TokenResponse（user_id + username + real_name + user_type + access_token）

    异常:
        40103: 用户名或密码错误（不区分具体原因，防止撞库枚举）
        40103: 账号已被禁用
    """
    # 1. 查用户（只用 username 查，因为 uk_username 唯一索引）
    user = db.query(SysUser).filter_by(username=username).first()

    # 2. 锁定检查（对应 API 文档 §4.2 规则4：连续 5 次失败锁定 30 分钟）
    if user and user.locked_until:
        now = datetime.now()
        if user.locked_until > now:
            remaining = int((user.locked_until - now).total_seconds() // 60) + 1
            raise AuthError(f"账户已锁定，请 {remaining} 分钟后重试")

    # 3. 用户名或密码错误 — 不告知具体是哪个错了（安全性：防撞库枚举）
    if user is None or not verify_password(password, user.password_hash):
        # 记录失败次数（用户存在时才记录）
        if user is not None:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=30)
            db.commit()
        raise AuthError("用户名或密码错误")

    # 4. 账号状态检查
    if user.status == "disabled":
        raise AuthError("账号已被禁用，请联系管理员")

    # 5. 签发 Token
    from config import ACCESS_TOKEN_EXPIRE_MINUTES

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        user_type=user.user_type,
        role_id=user.role_id,
    )

    # 6. 登录成功后：重置登录失败计数 + 清除锁定 + 更新最后登录时间
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()

    # 7. 返回 Token + 用户信息
    return TokenResponse(
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        user_type=user.user_type,
        role_id=user.role_id,
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 分钟 → 秒
    )


def get_current_user_info(db: Session, current_user: SysUser) -> UserMeResponse:
    """
    获取当前登录用户的详细信息。

    对应 API 文档第 4.3 节 GET /api/v1/auth/me。

    参数:
        db:           数据库会话
        current_user: 当前登录用户（由 get_current_user 依赖注入获得）

    返回:
        UserMeResponse，字段对齐 sys_user 表
    """
    return UserMeResponse(
        user_id=current_user.id,
        username=current_user.username,
        real_name=current_user.real_name,
        user_type=current_user.user_type,
        department=current_user.department,
        contact_info=current_user.contact_info,
        avatar_url=current_user.avatar_url,
        status=current_user.status,
    )


# ============================================================
# 二、用户管理 CRUD
# ============================================================


def create_user(db: Session, data: UserCreate) -> SysUser:
    """
    创建新用户。

    业务规则:
      1. username 唯一（uk_username 唯一索引兜底）
      2. 如果传了 role_id，校验 sys_role 记录存在（无物理外键策略）
      3. 密码用 bcrypt 哈希后存储

    参数:
        db:   数据库会话
        data: 用户创建请求体

    返回:
        新创建的 SysUser ORM 对象
    """
    # 1. 校验用户名唯一
    existing = db.query(SysUser).filter_by(username=data.username).first()
    if existing:
        raise ConflictError(f"用户名已存在: {data.username}")

    # 2. ⭐ 逻辑外键校验：如果传了 role_id，确认角色存在
    if data.role_id is not None:
        role = db.query(SysRole).filter_by(id=data.role_id).first()
        if not role:
            raise ReferenceNotFoundError("角色", data.role_id)

    # 3. 创建用户（密码 bcrypt 哈希）
    user = SysUser(
        username=data.username,
        password_hash=hash_password(data.password),  # 明文 → bcrypt 哈希
        real_name=data.real_name,
        user_type=data.user_type,
        role_id=data.role_id,
        department=data.department,
        contact_info=data.contact_info,
        avatar_url=data.avatar_url,
        status="normal",  # 新建用户默认状态 = normal
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user(db: Session, user_id: int) -> SysUser:
    """
    根据 ID 查询单个用户。

    参数:
        db:      数据库会话
        user_id: 用户主键

    返回:
        SysUser ORM 对象

    异常:
        NotFoundError: 用户不存在
    """
    user = db.query(SysUser).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError(f"用户不存在: id={user_id}")
    return user


def list_users(
    db: Session,
    pagination: PaginationParams,
    user_type: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    分页查询用户列表。

    支持筛选:
      - user_type: 按用户类型过滤（student / employee / admin）
      - keyword:   模糊搜索（匹配 username 或 real_name）
      - status:    按状态过滤（normal / disabled）

    参数:
        db:         数据库会话
        pagination: 分页参数（page, page_size）
        user_type:  用户类型筛选
        keyword:    关键词搜索
        status:     状态筛选

    返回:
        {items: [...], total: int, page: int, page_size: int}
    """
    # 构建基础查询
    query = db.query(SysUser)

    # 应用可选筛选条件（动态构建 WHERE 子句）
    if user_type:
        query = query.filter(SysUser.user_type == user_type)
    if status:
        query = query.filter(SysUser.status == status)
    if keyword:
        # LIKE 模糊搜索：匹配 username 或 real_name
        like_pattern = f"%{keyword}%"
        from sqlalchemy import or_

        query = query.filter(
            or_(
                SysUser.username.like(like_pattern),
                SysUser.real_name.like(like_pattern),
            )
        )

    # 总数（在分页前查询，不受 LIMIT/OFFSET 影响）
    total = query.count()

    # 分页 + 排序（按创建时间倒序，最新的在前）
    users = (
        query.order_by(SysUser.create_time.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    # 转成 Pydantic Schema 列表（不直接返回 ORM 对象，解耦前端与数据库结构）
    items = [UserResponse.model_validate(u).model_dump() for u in users]

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }


def update_user(db: Session, user_id: int, data: UserUpdate) -> SysUser:
    """
    更新用户信息（部分更新 — 只修改传入的字段）。

    业务规则:
      1. 只更新 data 中非 None 的字段（部分更新语义）
      2. 如果传了 role_id，校验角色存在（无物理外键策略）
      3. 不在此接口中修改密码（密码修改走专门的 change_password）

    参数:
        db:      数据库会话
        user_id: 用户主键
        data:    用户更新请求体（只含需修改的字段）

    返回:
        更新后的 SysUser ORM 对象
    """
    # 1. 查用户
    user = get_user(db, user_id)

    # 2. ⭐ 逻辑外键校验：如果传了 role_id，确认角色存在
    if data.role_id is not None:
        role = db.query(SysRole).filter_by(id=data.role_id).first()
        if not role:
            raise ReferenceNotFoundError("角色", data.role_id)

    # 3. 只更新非 None 字段（部分更新）
    update_data = data.model_dump(exclude_unset=True)  # exclude_unset=True: 只返回实际传入的字段
    for field, value in update_data.items():
        setattr(user, field, value)

    # 4. 提交事务
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# 三、角色查询
# ============================================================


def list_roles(db: Session) -> List[RoleResponse]:
    """
    查询所有启用的角色。

    角色数据量小（5 条），直接全量返回，不分页。
    未来如果角色数量增长，可加分页参数。

    返回:
        角色列表（仅 status=1 的启用角色）

    性能说明:
      角色列表适合缓存（应用启动时加载到内存）。
      见数据库文档第 13.3 节热点数据缓存策略。
    """
    roles = db.query(SysRole).filter_by(status=1).order_by(SysRole.id).all()
    return [RoleResponse.model_validate(r) for r in roles]


# ============================================================
# 四、组织架构管理
# ============================================================


def create_organization(db: Session, data: OrganizationCreate) -> SysOrganization:
    """
    创建组织节点。

    业务规则:
      1. 如果传了 parent_id，校验父节点存在（无物理外键策略）
      2. sort_order 默认 0

    参数:
        db:   数据库会话
        data: 组织创建请求体

    返回:
        新创建的 SysOrganization ORM 对象
    """
    # 1. ⭐ 逻辑外键校验：如果指定了父节点，确认父节点存在
    if data.parent_id is not None:
        parent = db.query(SysOrganization).filter_by(id=data.parent_id).first()
        if not parent:
            raise ReferenceNotFoundError("上级组织", data.parent_id)

    # 2. 创建组织节点
    org = SysOrganization(
        org_name=data.org_name,
        parent_id=data.parent_id,
        org_type=data.org_type,
        sort_order=data.sort_order,
        status=1,  # 新建组织默认启用
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    return org


def list_organizations_flat(db: Session) -> List[OrganizationResponse]:
    """
    平铺查询所有启用的组织节点。

    不分页（组织数量通常不大），用于前端下拉菜单或树形组件自行组装。

    返回:
        所有 status=1 的组织节点列表（平铺，不含 children）
    """
    orgs = (
        db.query(SysOrganization)
        .filter_by(status=1)
        .order_by(SysOrganization.sort_order, SysOrganization.id)
        .all()
    )
    return [OrganizationResponse.model_validate(o) for o in orgs]


def get_organization_tree(db: Session) -> List[OrganizationResponse]:
    """
    查询完整组织架构树（递归嵌套）。

    从根节点（parent_id IS NULL）开始，递归加载所有子节点。
    用于前端树形组件直接渲染，无需前端自行组装。

    算法:
      1. 查所有 status=1 的组织 → 全量加载到内存
      2. 从根节点开始 BFS/DFS 递归组装 children
      3. 返回树根列表

    为什么不全量查一次然后内存组装？
      组织数量通常在 100 以内，一次查询比 N+1 查询快几个数量级。

    返回:
        树形组织节点列表（根节点，children 递归嵌套）
    """
    # 1. 一次查询加载所有启用组织
    all_orgs = (
        db.query(SysOrganization)
        .filter_by(status=1)
        .order_by(SysOrganization.sort_order, SysOrganization.id)
        .all()
    )

    if not all_orgs:
        return []

    # 2. 构建 id → 节点的映射表（方便 O(1) 查找子节点）
    node_map: Dict[int, OrganizationResponse] = {}
    for org in all_orgs:
        node_map[org.id] = OrganizationResponse.model_validate(org)

    # 3. 组装树：遍历所有节点，挂到各自 parent 的 children 下
    roots: List[OrganizationResponse] = []
    for org in all_orgs:
        node = node_map[org.id]
        if org.parent_id is not None and org.parent_id in node_map:
            # 有父节点 → 挂到父节点的 children 列表
            parent_node = node_map[org.parent_id]
            parent_node.children.append(node)
        else:
            # 无父节点（或父节点已删除/禁用）→ 作为根节点
            roots.append(node)

    return roots


# ============================================================
# 六、密码修改
# ============================================================


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> None:
    """
    修改用户密码。

    业务流程:
      1. 查用户
      2. 验证旧密码（防止未授权修改）
      3. bcrypt 哈希新密码 → 更新入库

    参数:
        db:          数据库会话
        user_id:     要修改密码的用户 ID
        old_password: 当前密码（用于身份验证）
        new_password: 新密码
    """
    user = db.query(SysUser).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError(f"用户不存在: id={user_id}")

    if not verify_password(old_password, user.password_hash):
        raise AuthError("旧密码错误")

    user.password_hash = hash_password(new_password)
    db.commit()


# ============================================================
# 五、种子数据初始化
# ============================================================


def seed_data(db: Session) -> None:
    """
    应用启动时自动初始化种子数据（仅当表为空时才插入，已有数据则跳过）。

    对应数据库设计文档第 11 章：
      - sys_role:  5 条角色（admin/employee/manager/team_leader/student）
      - sys_user:  1 个管理员（admin / admin123）

    设计要点:
      使用了"先查后插"的幂等逻辑——每次启动都调用，但只有表为空时才插入。
      这样不会因重复启动而创建重复数据。

    测试用户（文档第 11.4 节）：
      admin     / admin123  — 系统管理员
      employee1 / emp123    — 普通员工（后续按需添加）
      student1  / stu123    — 在读学生（后续按需添加）
    """
    # --- 1. 角色种子数据 ---
    if db.query(SysRole).count() == 0:
        roles = [
            SysRole(
                role_code="admin",
                role_name="系统管理员",
                description="最高权限，可管理所有模块和用户",
            ),
            SysRole(
                role_code="employee",
                role_name="员工",
                description="普通员工，可管理自己负责的客户",
            ),
            SysRole(
                role_code="manager",
                role_name="部门经理",
                description="管理人员，可查看本部门数据",
            ),
            SysRole(
                role_code="team_leader",
                role_name="班主任",
                description="学生班主任，负责学生请假审批和心理预警跟进",
            ),
            SysRole(
                role_code="student",
                role_name="学生",
                description="在校学生，可查看课程、提交请假和投诉",
            ),
        ]
        db.add_all(roles)
        db.commit()
        # 让 SQLAlchemy 知道这些对象已经有 id 了（后续可用 role.id）
        for r in roles:
            db.refresh(r)

    # --- 2. 管理员用户种子数据 ---
    if db.query(SysUser).filter_by(username="admin").count() == 0:
        # 找到 admin 角色
        admin_role = db.query(SysRole).filter_by(role_code="admin").first()
        admin = SysUser(
            username="admin",
            password_hash=hash_password("admin123"),
            real_name="系统管理员",
            user_type="admin",
            role_id=admin_role.id if admin_role else None,
            department="技术部",
            contact_info="admin@example.com",
            status="normal",
        )
        db.add(admin)
        db.commit()
