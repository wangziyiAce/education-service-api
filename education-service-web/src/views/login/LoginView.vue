<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const form = reactive({
  username: '',
  password: '',
})
const loading = ref(false)
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    const code = e?.code
    const msg = e?.message
    if (code === 40103 || (msg && msg.includes('密码'))) {
      ElMessage.error('密码错误，请重新输入')
    } else if (code === 40101 || code === 40401 || (msg && msg.includes('不存在'))) {
      ElMessage.error('用户名不存在')
    } else if (msg && msg.includes('禁用')) {
      ElMessage.error('账号已被禁用，请联系管理员')
    } else {
      ElMessage.error(msg || '登录失败，请检查用户名和密码')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="brand-content">
        <div class="brand-logo">
          <el-icon :size="64" color="rgba(255,255,255,0.85)"><School /></el-icon>
        </div>
        <h1 class="brand-title">教育服务系统</h1>
        <p class="brand-slogan">智能管理平台</p>
      </div>
      <!-- 装饰波浪 -->
      <div class="brand-wave">
        <svg viewBox="0 0 1440 120" preserveAspectRatio="none">
          <path
            d="M0,40 C240,100 480,0 720,60 C960,120 1200,20 1440,80 L1440,120 L0,120 Z"
            fill="rgba(255,255,255,0.06)"
          />
          <path
            d="M0,70 C180,30 360,110 540,70 C720,30 900,100 1080,60 C1260,20 1440,90 1440,90 L1440,120 L0,120 Z"
            fill="rgba(255,255,255,0.04)"
          />
        </svg>
      </div>
      <!-- 装饰圆点 -->
      <div class="brand-dots">
        <span class="dot" v-for="i in 15" :key="i" :style="{ animationDelay: i * 0.2 + 's' }"></span>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-panel">
      <div class="form-card">
        <h2 class="form-title">欢迎回来</h2>
        <p class="form-subtitle">请输入账号密码登录</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          class="login-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          没有账号？
          <router-link to="/register">去注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { User, Lock, School } from '@element-plus/icons-vue'
export default {
  components: { User, Lock, School },
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
  border-radius: 0;
}

/* ========== 左侧品牌区 ========== */
.brand-panel {
  position: relative;
  width: 40%;
  min-width: 320px;
  background: linear-gradient(160deg, #1a73e8 0%, #0d47a1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 0;
}

.brand-content {
  position: relative;
  z-index: 2;
  text-align: center;
}

.brand-logo {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.brand-title {
  margin: 0 0 12px;
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
}

.brand-slogan {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 4px;
}

/* 波浪装饰 */
.brand-wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 120px;
  z-index: 1;
  svg {
    width: 100%;
    height: 100%;
  }
}

/* 浮动圆点 */
.brand-dots {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.dot {
  position: absolute;
  width: 6px;
  height: 6px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  animation: float 4s ease-in-out infinite;

  &:nth-child(1)  { top: 12%; left: 10%; }
  &:nth-child(2)  { top: 22%; left: 75%; width: 4px; height: 4px; }
  &:nth-child(3)  { top: 35%; left: 20%; width: 8px; height: 8px; }
  &:nth-child(4)  { top: 48%; left: 85%; }
  &:nth-child(5)  { top: 60%; left: 15%; width: 5px; height: 5px; }
  &:nth-child(6)  { top: 72%; left: 55%; width: 7px; height: 7px; }
  &:nth-child(7)  { top: 85%; left: 30%; width: 4px; height: 4px; }
  &:nth-child(8)  { top: 8%;  left: 45%; width: 5px; height: 5px; }
  &:nth-child(9)  { top: 18%; left: 60%; width: 7px; height: 7px; }
  &:nth-child(10) { top: 42%; left: 40%; }
  &:nth-child(11) { top: 55%; left: 70%; width: 4px; height: 4px; }
  &:nth-child(12) { top: 78%; left: 10%; width: 8px; height: 8px; }
  &:nth-child(13) { top: 90%; left: 80%; width: 5px; height: 5px; }
  &:nth-child(14) { top: 28%; left: 35%; width: 6px; height: 6px; }
  &:nth-child(15) { top: 68%; left: 45%; width: 4px; height: 4px; }
}

@keyframes float {
  0%, 100% { transform: translateY(0); opacity: 0.15; }
  50% { transform: translateY(-12px); opacity: 0.4; }
}

/* ========== 右侧表单区 ========== */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 0;
}

.form-card {
  width: 100%;
  max-width: 380px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 0;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
}

.form-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.form-subtitle {
  margin: 0 0 32px;
  font-size: 14px;
  color: #909399;
}

.login-form {
  :deep(.el-input__wrapper) {
    border-radius: 0;
    box-shadow: 0 0 0 1px #dcdfe6;
    padding: 1px 11px;
    &:hover {
      box-shadow: 0 0 0 1px #c0c4cc;
    }
    &.is-focus {
      box-shadow: 0 0 0 1px #1a73e8;
    }
  }
  :deep(.el-form-item) {
    margin-bottom: 20px;
  }
  :deep(.el-form-item__error) {
    font-size: 12px;
  }
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  border-radius: 0;
  background: linear-gradient(135deg, #1a73e8, #0d47a1);
  border: none;
  &:hover {
    background: linear-gradient(135deg, #1565c0, #0a3d91);
  }
}

.form-footer {
  text-align: center;
  font-size: 13px;
  color: #909399;
  a {
    color: #1a73e8;
    text-decoration: none;
    font-weight: 500;
    &:hover {
      text-decoration: underline;
    }
  }
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .login-page {
    flex-direction: column;
  }

  .brand-panel {
    width: 100%;
    min-width: unset;
    height: 200px;
    flex-shrink: 0;
  }

  .brand-title {
    font-size: 22px;
  }

  .brand-slogan {
    font-size: 12px;
  }

  .brand-wave {
    height: 60px;
  }

  .form-panel {
    flex: 1;
    padding: 20px;
  }

  .form-card {
    max-width: 100%;
    padding: 32px 24px;
    box-shadow: none;
  }
}
</style>
