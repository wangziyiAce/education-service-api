<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { authApi } from '@/api/auth'
import type { UserInfo, RoleInfo } from '@/types/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ---------- 用户列表 ---------- */
const users = ref<UserInfo[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

/* ---------- 角色列表 ---------- */
const roles = ref<RoleInfo[]>([])
const roleCodeToId = ref<Record<string, number>>({})
const roleIdToCode = ref<Record<number, string>>({})
const roleCodes = ref<string[]>([])

const roleLabelMap: Record<string, string> = {
  customer: '客户',
  student: '学员',
  employee: '员工',
  manager: '经理',
  team_leader: '教导主任',
  admin: '管理员',
}

/* ---------- 切换中的角色（用于 el-select v-model 绑定到行） ---------- */
const pendingRole = ref<Record<number, string>>({})

/* ---------- 用户类型标签颜色 ---------- */
function getUserTypeTagType(userType: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    customer: 'success',
    student: '',
    employee: 'warning',
    manager: 'warning',
    team_leader: 'primary',
    admin: 'danger',
  }
  return map[userType] ?? 'info'
}

function getUserTypeLabel(userType: string): string {
  const map: Record<string, string> = {
    customer: '客户',
    student: '学员',
    employee: '员工',
    manager: '经理',
    team_leader: '教导主任',
    admin: '管理员',
  }
  return map[userType] ?? userType
}

/* ---------- 获取角色列表 ---------- */
async function fetchRoles() {
  try {
    const res: any = await authApi.listRoles()
    // API 返回 {items: [...]} 或直接是数组
    const list: RoleInfo[] = Array.isArray(res) ? res : (res?.items ?? [])
    roles.value = list
    const codeToId: Record<string, number> = {}
    const idToCode: Record<number, string> = {}
    const codes: string[] = []
    for (const r of list) {
      codeToId[r.role_code] = r.id
      idToCode[r.id] = r.role_code
      codes.push(r.role_code)
    }
    roleCodeToId.value = codeToId
    roleIdToCode.value = idToCode
    roleCodes.value = codes
  } catch {
    roles.value = []
  }
}

/* ---------- 获取用户列表 ---------- */
async function fetchUsers() {
  loading.value = true
  try {
    const res: any = await authApi.listUsers({ page: currentPage.value, page_size: pageSize.value })
    // API 返回 {items, total} 或直接数组
    const list: UserInfo[] = Array.isArray(res) ? res : (res?.items ?? [])
    users.value = list
    total.value = res?.total ?? list.length
    // 初始化每个用户当前角色（role_id -> role_code）
    for (const u of users.value) {
      const code = u.role_id != null ? (roleIdToCode.value[u.role_id] ?? '') : ''
      pendingRole.value[u.id] = code
    }
  } catch {
    users.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/* ---------- 角色切换 ---------- */
async function handleRoleChange(newRoleCode: string, user: UserInfo) {
  if (!newRoleCode) return

  const roleId = roleCodeToId.value[newRoleCode]
  if (roleId === undefined) {
    ElMessage.error('无效的角色')
    return
  }

  if (roleId === user.role_id) return // 未变化

  // role_code 和 user_type 保持一致
  const newUserType = newRoleCode

  try {
    await authApi.updateUser(user.id, { role_id: roleId, user_type: newUserType })
    user.role_id = roleId
    user.user_type = newUserType as any
    ElMessage.success('角色更新成功')
  } catch {
    // 还原
    pendingRole.value[user.id] = roleIdToCode.value[user.role_id ?? 0] ?? ''
    ElMessage.error('角色更新失败')
  }
}

/* ---------- 重置密码 ---------- */
const passwordDialogVisible = ref(false)
const resetPasswordUser = ref<UserInfo | null>(null)
const newPassword = ref('')
const resetting = ref(false)

function openPasswordDialog(user: UserInfo) {
  resetPasswordUser.value = user
  newPassword.value = ''
  passwordDialogVisible.value = true
}

async function handleResetPassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }
  resetting.value = true
  try {
    await authApi.resetPassword(resetPasswordUser.value!.id, newPassword.value)
    ElMessage.success('密码重置成功')
    passwordDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || '重置失败')
  } finally {
    resetting.value = false
  }
}

/* ---------- 分页 ---------- */
function handlePageChange(page: number) {
  currentPage.value = page
  fetchUsers()
}

/* ---------- 内联编辑 ---------- */
const editingCell = ref<{ userId: number; field: string } | null>(null)
const editValue = ref('')

function startEdit(userId: number, field: string, currentValue: string) {
  editingCell.value = { userId, field }
  editValue.value = currentValue
}

async function saveEdit(user: UserInfo) {
  if (!editingCell.value) return
  const { field } = editingCell.value
  const newVal = editValue.value.trim()
  editingCell.value = null

  if (!newVal || newVal === (user as any)[field]) return

  try {
    await authApi.updateUser(user.id, { [field]: newVal })
    ;(user as any)[field] = newVal
    ElMessage.success('更新成功')
  } catch {
    ElMessage.error('更新失败')
  }
}

function cancelEdit() {
  editingCell.value = null
}

function handleEditKeydown(event: KeyboardEvent, user: UserInfo) {
  if (event.key === 'Enter') { saveEdit(user) }
  if (event.key === 'Escape') { cancelEdit() }
}
async function handleToggleStatus(user: UserInfo) {
  const newStatus = user.status === 'normal' ? 'disabled' : 'normal'
  const actionText = newStatus === 'disabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确认${actionText}用户「${user.real_name || user.username}」？`,
      `${actionText}确认`,
      { confirmButtonText: actionText, cancelButtonText: '取消', type: 'warning' }
    )
    await authApi.updateUser(user.id, { status: newStatus })
    user.status = newStatus
    ElMessage.success(`${actionText}成功`)
  } catch {
    // 取消或失败
  }
}

/* ---------- 初始化 ---------- */
onMounted(async () => {
  await fetchRoles()
  await fetchUsers()
})
</script>

<template>
  <div class="user-management">
    <PageHeader>
      <template #actions>
        <span style="color: #909399; font-size: 13px">仅管理员可见</span>
      </template>
    </PageHeader>

    <div class="user-management__body">
      <el-table
        :data="users"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />

        <el-table-column prop="username" label="用户名" min-width="160">
          <template #default="{ row }">
            <template v-if="!(editingCell && editingCell.userId === row.id && editingCell.field === 'username')">
              <span class="editable-cell" style="font-weight:500;cursor:pointer" @click="startEdit(row.id,'username',row.username)">
                {{ row.username }} <el-icon class="edit-hint"><EditPen /></el-icon>
              </span>
            </template>
            <template v-else>
              <div class="edit-inline">
                <el-input v-model="editValue" size="small" style="width:120px" @keydown.enter="saveEdit(row)" />
                <el-button size="small" type="primary" @click="saveEdit(row)">确认</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </template>
          </template>
        </el-table-column>

        <el-table-column prop="real_name" label="真实姓名" min-width="160">
          <template #default="{ row }">
            <template v-if="!(editingCell && editingCell.userId === row.id && editingCell.field === 'real_name')">
              <span class="editable-cell" style="cursor:pointer" @click="startEdit(row.id,'real_name',row.real_name||'')">
                {{ row.real_name || '—' }} <el-icon class="edit-hint"><EditPen /></el-icon>
              </span>
            </template>
            <template v-else>
              <div class="edit-inline">
                <el-input v-model="editValue" size="small" style="width:120px" @keydown.enter="saveEdit(row)" />
                <el-button size="small" type="primary" @click="saveEdit(row)">确认</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </template>
          </template>
        </el-table-column>

        <el-table-column prop="department" label="部门" min-width="160">
          <template #default="{ row }">
            <template v-if="!(editingCell && editingCell.userId === row.id && editingCell.field === 'department')">
              <span class="editable-cell" style="cursor:pointer" @click="startEdit(row.id,'department',row.department||'')">
                {{ row.department || '—' }} <el-icon class="edit-hint"><EditPen /></el-icon>
              </span>
            </template>
            <template v-else>
              <div class="edit-inline">
                <el-input v-model="editValue" size="small" style="width:120px" @keydown.enter="saveEdit(row)" />
                <el-button size="small" type="primary" @click="saveEdit(row)">确认</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </template>
          </template>
        </el-table-column>

        <el-table-column label="用户类型" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getUserTypeTagType(row.user_type)"
              size="small"
            >
              {{ getUserTypeLabel(row.user_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="180">
          <template #default="{ row }">
            <el-select
              v-model="pendingRole[row.id]"
              size="small"
              placeholder="选择角色"
              style="width: 140px"
              @change="(val: string) => handleRoleChange(val, row)"
            >
              <el-option
                v-for="code in roleCodes"
                :key="code"
                :label="roleLabelMap[code] ?? code"
                :value="code"
              />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'normal' ? 'success' : 'danger'" size="small">
              {{ row.status === 'normal' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="密码" width="80">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click.stop="openPasswordDialog(row)">
              重置
            </el-button>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.status === 'normal' ? 'danger' : 'success'"
              size="small"
              plain
              @click.stop="handleToggleStatus(row)"
            >
              {{ row.status === 'normal' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="user-management__pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="400px">
      <p>用户：{{ resetPasswordUser?.real_name || resetPasswordUser?.username }}</p>
      <el-input v-model="newPassword" type="password" placeholder="请输入新密码（至少6位）" show-password />
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="handleResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.user-management {
  max-width: 1200px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    margin-top: 16px;
  }

  &__pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
.editable-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 4px;
  &:hover {
    background: #f0f5ff;
    .edit-hint { opacity: 1; }
  }
}
.edit-hint {
  opacity: 0;
  font-size: 12px;
  color: #409eff;
  transition: opacity 0.2s;
}
.edit-inline {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
