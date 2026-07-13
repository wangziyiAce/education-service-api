<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/api/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()

const userLabelMap: Record<string, string> = {
  customer: '客户', student: '学员', employee: '员工',
  manager: '经理', team_leader: '教导主任', admin: '管理员',
}

/* ---------- 基本信息编辑 ---------- */
const editing = ref(false)
const saving = ref(false)
const form = reactive({
  real_name: auth.user?.real_name || '',
  department: auth.user?.department || '',
  contact_info: auth.user?.contact_info || '',
})

function startEdit() {
  form.real_name = auth.user?.real_name || ''
  form.department = auth.user?.department || ''
  form.contact_info = auth.user?.contact_info || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveProfile() {
  saving.value = true
  try {
    await authApi.updateUser(auth.user!.id, {
      real_name: form.real_name,
      contact_info: form.contact_info,
    })
    if (auth.user) {
      auth.user.real_name = form.real_name || null
      auth.user.department = form.department || null
      auth.user.contact_info = form.contact_info || null
    }
    ElMessage.success('保存成功')
    editing.value = false
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

/* ---------- 修改密码 ---------- */
const passwordDialog = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const changingPassword = ref(false)

function openPasswordDialog() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordDialog.value = true
}

async function changePassword() {
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码至少6位')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次密码不一致')
    return
  }
  changingPassword.value = true
  try {
    await authApi.changePassword(auth.user!.id, {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordDialog.value = false
    auth.logout()
  } catch (e: any) {
    ElMessage.error(e?.message || '修改失败，请检查旧密码是否正确')
  } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <PageHeader />
    <div class="profile-page__body">
      <!-- 基本信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <div>
              <el-button v-if="!editing" type="primary" size="small" @click="startEdit">编辑</el-button>
              <template v-else>
                <el-button size="small" @click="cancelEdit">取消</el-button>
                <el-button type="primary" size="small" :loading="saving" @click="saveProfile">保存</el-button>
              </template>
            </div>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ auth.user?.username }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag size="small">{{ userLabelMap[auth.userType] || auth.userType }}</el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="真实姓名">
            <template v-if="editing">
              <el-input v-model="form.real_name" placeholder="请输入真实姓名" size="small" />
            </template>
            <template v-else>{{ auth.user?.real_name || '—' }}</template>
          </el-descriptions-item>

          <el-descriptions-item label="部门">{{ auth.user?.department || '—' }}</el-descriptions-item>

          <el-descriptions-item label="联系方式" :span="2">
            <template v-if="editing">
              <el-input v-model="form.contact_info" placeholder="手机号/邮箱" size="small" />
            </template>
            <template v-else>{{ auth.user?.contact_info || '—' }}</template>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 修改密码卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>账号安全</span>
          </div>
        </template>
        <el-button type="warning" @click="openPasswordDialog">修改密码</el-button>
      </el-card>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="passwordDialog" title="修改密码" width="420px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="旧密码" required>
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialog = false">取消</el-button>
        <el-button type="primary" :loading="changingPassword" @click="changePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.profile-page {
  max-width: 800px;
  margin: 0 auto;
  &__body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 16px;
  }
}
.info-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
