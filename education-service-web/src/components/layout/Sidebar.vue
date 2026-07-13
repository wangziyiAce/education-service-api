<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { computed, ref } from 'vue'

const router = useRouter()
const auth = useAuthStore()

const isCollapsed = ref(false)

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

interface MenuItem {
  path: string
  title: string
  icon: string
  roles?: string[]
}

const allMenuItems: MenuItem[] = [
  { path: '/dashboard', title: '首页看板', icon: 'DataAnalysis' },
  { path: '/profile', title: '个人信息', icon: 'User' },

  { path: '/courses', title: '课程浏览', icon: 'Reading', roles: ['customer', 'student', 'employee', 'manager', 'team_leader', 'admin'] },
  { path: '/events', title: '活动浏览', icon: 'Calendar', roles: ['customer', 'student', 'employee', 'manager', 'team_leader', 'admin'] },
  { path: '/chat', title: '智能客服', icon: 'ChatDotRound', roles: ['customer'] },

  { path: '/student-assistant', title: '学生智能助手', icon: 'ChatDotSquare', roles: ['student'] },

  { path: '/crm/leads', title: '客户管理', icon: 'UserFilled', roles: ['employee', 'manager', 'team_leader', 'admin'] },
  { path: '/assistant', title: '企业智能助手', icon: 'ChatLineSquare', roles: ['employee', 'manager', 'team_leader', 'admin'] },
  { path: '/student/leaves', title: '请假管理', icon: 'Document', roles: ['employee', 'manager', 'team_leader', 'admin'] },
  { path: '/student/feedbacks', title: '投诉管理', icon: 'Warning', roles: ['employee', 'manager', 'team_leader', 'admin'] },
  { path: '/profile/upload', title: '客户研判', icon: 'Upload', roles: ['employee', 'manager', 'team_leader', 'admin'] },
  { path: '/reports', title: '报告中心', icon: 'DataLine', roles: ['employee', 'manager', 'team_leader', 'admin'] },

  { path: '/student/psych-alerts', title: '心理预警', icon: 'Bell', roles: ['manager', 'team_leader', 'admin'] },

  { path: '/admin/users', title: '用户管理', icon: 'Setting', roles: ['admin'] },
]

const menuItems = computed(() => {
  const userType = auth.userType
  return allMenuItems.filter(item => {
    if (!item.roles) return true
    return item.roles.includes(userType)
  })
})

const userRoleLabel = computed(() => {
  const map: Record<string, string> = {
    admin: '管理员',
    manager: '经理',
    team_leader: '组长',
    employee: '员工',
    customer: '客户',
    student: '学生',
  }
  return map[auth.userType] || auth.userType || '用户'
})

const userRoleTagType = computed(() => {
  const map: Record<string, string> = {
    admin: 'danger',
    customer: 'success',
    student: '',
    employee: 'warning',
    manager: 'warning',
    team_leader: 'warning',
  }
  return map[auth.userType] || 'info'
})

function navigate(path: string) {
  router.push(path)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': isCollapsed }">
    <!-- Logo 区 -->
    <div class="sidebar__logo" @click="navigate('/dashboard')">
      <el-icon :size="24" class="sidebar__logo-icon"><DataAnalysis /></el-icon>
      <transition name="fade">
        <h1 v-show="!isCollapsed" class="sidebar__logo-text">教育服务系统</h1>
      </transition>
    </div>

    <!-- 菜单区 -->
    <div class="sidebar__menu">
      <div
        v-for="item in menuItems"
        :key="item.path"
        class="sidebar__menu-item"
        :class="{ 'sidebar__menu-item--active': $route.path === item.path }"
        @click="navigate(item.path)"
      >
        <el-icon :size="18"><component :is="item.icon" /></el-icon>
        <span v-show="!isCollapsed" class="sidebar__menu-title">{{ item.title }}</span>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="sidebar__bottom">
      <!-- 用户信息 -->
      <div class="sidebar__user" @click="navigate('/profile')">
        <el-avatar :size="isCollapsed ? 28 : 32" icon="UserFilled" />
        <transition name="fade">
          <div v-show="!isCollapsed" class="sidebar__user-info">
            <span class="sidebar__user-name">{{ auth.realName || '用户' }}</span>
            <el-tag :type="userRoleTagType" size="small" class="sidebar__user-role">{{ userRoleLabel }}</el-tag>
          </div>
        </transition>
      </div>

      <!-- 退出 + 收起 -->
      <div class="sidebar__actions">
        <transition name="fade">
          <el-button
            v-show="!isCollapsed"
            type="danger"
            text
            size="small"
            @click="handleLogout"
          >
            退出登录
          </el-button>
        </transition>
        <div class="sidebar__collapse-btn" @click="toggleCollapse">
          <el-icon :size="16">
            <ArrowLeft v-if="!isCollapsed" />
            <ArrowRight v-else />
          </el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: linear-gradient(180deg, #1e293b 0%, #304156 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(.4,0,.2,1);
  position: relative;
  flex-shrink: 0;

  &--collapsed {
    width: 60px;
  }

  // ---- Logo ----
  &__logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 18px 16px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255,255,255,.08);
    min-height: 60px;
    justify-content: center;
  }
  &__logo-icon {
    color: #60a5fa;
    flex-shrink: 0;
  }
  &__logo-text {
    color: #fff;
    font-size: 15px;
    font-weight: 700;
    margin: 0;
    white-space: nowrap;
    letter-spacing: 0.5px;
  }

  // ---- 菜单 ----
  &__menu {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 8px 0;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,.12);
      border-radius: 2px;
    }
  }
  &__menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 3px 10px;
    padding: 10px 14px;
    border-radius: 10px;
    color: rgba(255,255,255,.65);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    white-space: nowrap;
    font-size: 14px;
    min-height: 42px;
    justify-content: center;

    .sidebar:not(.sidebar--collapsed) & {
      justify-content: flex-start;
    }

    &:hover {
      background: rgba(255,255,255,.08);
      color: #fff;
    }

    &--active {
      background: rgba(255,255,255,.15);
      color: #fff;
      font-weight: 600;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: #60a5fa;
        border-radius: 0 3px 3px 0;
      }
    }
  }
  &__menu-title {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  // ---- 底部 ----
  &__bottom {
    border-top: 1px solid rgba(255,255,255,.08);
    padding: 8px 0;
    flex-shrink: 0;
  }
  &__user {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    cursor: pointer;
    transition: background 0.2s ease;
    border-radius: 0;
    justify-content: center;

    .sidebar:not(.sidebar--collapsed) & {
      justify-content: flex-start;
    }

    &:hover {
      background: rgba(255,255,255,.06);
    }
  }
  &__user-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow: hidden;
  }
  &__user-name {
    font-size: 13px;
    color: #fff;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  &__user-role {
    width: fit-content;
    font-size: 11px;
  }

  // ---- 操作按钮 ----
  &__actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 10px;

    .sidebar--collapsed & {
      justify-content: center;
    }
  }
  &__collapse-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    color: rgba(255,255,255,.45);
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;

    &:hover {
      background: rgba(255,255,255,.1);
      color: #fff;
    }
  }
}
</style>
