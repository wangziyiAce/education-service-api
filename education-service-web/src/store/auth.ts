import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userType = computed(() => user.value?.user_type ?? 'visitor')
  const realName = computed(() => user.value?.real_name ?? user.value?.username ?? '')

  async function login(username: string, password: string) {
    const res: any = await authApi.login({ username, password })
    token.value = res.access_token
    // API 返回的 data 中用户字段是扁平结构，手动映射为 UserInfo
    user.value = {
      id: res.user_id,
      username: res.username,
      real_name: res.real_name,
      user_type: res.user_type,
      role_id: res.role_id ?? null,
      department: res.department ?? null,
      contact_info: res.contact_info ?? null,
      avatar_url: res.avatar_url ?? null,
      status: 'normal',
    }
    localStorage.setItem('access_token', res.access_token)
    return res
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  async function restoreFromToken() {
    try {
      const res: any = await authApi.getMe()
      user.value = {
        id: res.user_id ?? res.id,
        username: res.username,
        real_name: res.real_name,
        user_type: res.user_type,
        role_id: res.role_id ?? null,
        department: res.department ?? null,
        contact_info: res.contact_info ?? null,
        avatar_url: res.avatar_url ?? null,
        status: res.status ?? 'normal',
      }
    } catch {
      logout()
      throw new Error('Token 已失效')
    }
  }

  function hasAnyRole(roles: string[]): boolean {
    if (!user.value) return false
    return roles.includes(user.value.user_type)
  }

  return {
    user,
    token,
    isLoggedIn,
    userType,
    realName,
    login,
    logout,
    restoreFromToken,
    hasAnyRole,
  }
})
