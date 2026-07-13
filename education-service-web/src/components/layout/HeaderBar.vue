<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const userName = computed(() => auth.realName || '未登录')

// 模拟通知数据（后续接入真实 API）
const notifications = ref([
  { id: 1, title: '系统通知', content: '欢迎使用教育服务系统', time: '2026-07-12 10:00' },
])
const unreadCount = computed(() => notifications.value.length)

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function goToNotifications() {
  ElMessage.info('通知中心功能（P1 开发中）')
}
</script>

<template>
  <div class="header-bar">
    <div class="header-bar__left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-bar__right">
      <!-- 通知铃铛 -->
      <el-popover placement="bottom-end" :width="320" trigger="click">
        <template #reference>
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="header-bar__bell">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
        </template>
        <div class="notification-popover">
          <div class="notification-popover__header">
            <span>消息通知</span>
            <el-button text type="primary" size="small" @click="goToNotifications">查看全部</el-button>
          </div>
          <div class="notification-popover__list" v-if="notifications.length">
            <div v-for="item in notifications" :key="item.id" class="notification-popover__item">
              <div class="notification-popover__title">{{ item.title }}</div>
              <div class="notification-popover__content">{{ item.content }}</div>
              <div class="notification-popover__time">{{ item.time }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无通知" :image-size="60" />
        </div>
      </el-popover>

      <!-- 用户菜单 -->
      <el-dropdown trigger="click" class="header-bar__user-dropdown">
        <span class="header-bar__user">
          <el-tag size="small" :type="auth.userType === 'admin' ? 'danger' : auth.userType === 'customer' ? 'success' : auth.userType === 'student' ? '' : 'warning'">{{ auth.userType }}</el-tag>
          <el-icon><UserFilled /></el-icon>
          {{ userName }}
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="navigate('/profile')">个人信息</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.header-bar {
  height: 56px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  transition: background 0.3s ease;

  &__left {
    display: flex;
    align-items: center;

    :deep(.el-breadcrumb) {
      font-size: 13px;
      .el-breadcrumb__item:last-child .el-breadcrumb__inner {
        color: var(--color-text);
        font-weight: 600;
      }
    }
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  &__bell {
    cursor: pointer;
    color: #606266;
    transition: color 0.2s ease, transform 0.2s ease;
    &:hover {
      color: #409eff;
      transform: scale(1.1);
    }
  }

  &__user {
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 8px;
    transition: background 0.2s ease;
    font-size: 14px;

    &:hover {
      background: rgba(0, 0, 0, 0.04);
    }
  }

  &__user-dropdown {
    margin-left: 0;
  }
}

.notification-popover {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid #ebeef5;
    font-weight: 600;
  }
  &__list { max-height: 300px; overflow-y: auto; }
  &__item {
    padding: 10px 0;
    border-bottom: 1px solid #f5f5f5;
    cursor: pointer;
    &:hover { background: #f5f7fa; }
    &:last-child { border-bottom: none; }
  }
  &__title { font-size: 13px; color: #303133; }
  &__content { font-size: 12px; color: #909399; margin-top: 4px; }
  &__time { font-size: 11px; color: #c0c4cc; margin-top: 4px; }
}
</style>
