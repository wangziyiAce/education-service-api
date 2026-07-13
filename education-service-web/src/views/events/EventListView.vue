<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api/chat'
import type { Event, EventRegistrationCreate } from '@/types/chat'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const router = useRouter()

// ---------- 搜索 & 分页 ----------
const statusFilter = ref<string>('')
const typeFilter = ref<string>('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const events = ref<Event[]>([])
const loading = ref(false)

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '即将开始', value: 'upcoming' },
  { label: '进行中', value: 'ongoing' },
  { label: '已结束', value: 'ended' },
  { label: '已取消', value: 'cancelled' },
]

const typeOptions = [
  { label: '全部类型', value: '' },
  { label: '线上', value: 'online' },
  { label: '线下', value: 'offline' },
  { label: '混合', value: 'hybrid' },
]

const typeLabelMap: Record<string, string> = {
  online: '线上',
  offline: '线下',
  hybrid: '混合',
}

// ---------- 获取列表 ----------
async function fetchEvents() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value) params.event_type = typeFilter.value
    const res = await chatApi.listEvents(params)
    events.value = res.items
    total.value = res.total
  } catch {
    // 错误已在 request 拦截器中统一处理
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchEvents()
}

function handleReset() {
  statusFilter.value = ''
  typeFilter.value = ''
  currentPage.value = 1
  fetchEvents()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchEvents()
}

// ---------- 报名弹窗 ----------
const registerDialogVisible = ref(false)
const registerEventId = ref<number>(0)
const registerEventName = ref('')
const registerLoading = ref(false)

const registerForm = reactive<EventRegistrationCreate>({
  customer_name: '',
  contact_info: '',
  remark: '',
})

function openRegisterDialog(event: Event) {
  registerEventId.value = event.id
  registerEventName.value = event.event_name
  registerForm.customer_name = ''
  registerForm.contact_info = ''
  registerForm.remark = ''
  registerDialogVisible.value = true
}

async function handleRegister() {
  if (!registerForm.customer_name || !registerForm.contact_info) {
    ElMessage.warning('请填写姓名和联系方式')
    return
  }
  registerLoading.value = true
  try {
    await chatApi.registerEvent(registerEventId.value, { ...registerForm })
    ElMessage.success('报名成功')
    registerDialogVisible.value = false
    fetchEvents()
  } catch {
    // 错误已在 request 拦截器中统一处理
  } finally {
    registerLoading.value = false
  }
}

// ---------- 跳转详情 ----------
function goDetail(id: number) {
  router.push(`/events/${id}`)
}

// ---------- 格式化时间 ----------
function formatTime(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  fetchEvents()
})
</script>

<template>
  <div class="event-list">
    <PageHeader />

    <!-- 搜索栏 -->
    <div class="event-list__toolbar">
      <div class="event-list__filters">
        <el-select
          v-model="statusFilter"
          placeholder="活动状态"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option
            v-for="opt in statusOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-select
          v-model="typeFilter"
          placeholder="活动类型"
          clearable
          style="width: 140px; margin-left: 12px"
          @change="handleSearch"
        >
          <el-option
            v-for="opt in typeOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-button style="margin-left: 12px" @click="handleReset">重置</el-button>
      </div>
    </div>

    <!-- 卡片列表 -->
    <div class="event-list__body" v-loading="loading">
      <template v-if="events.length">
        <el-row :gutter="20">
          <el-col
            v-for="item in events"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            style="margin-bottom: 20px"
          >
            <el-card shadow="hover" class="event-card">
              <div class="event-card__header">
                <span class="event-card__name">{{ item.event_name }}</span>
                <el-tag size="small" type="info" style="margin-left: 8px">
                  {{ typeLabelMap[item.event_type] || item.event_type }}
                </el-tag>
              </div>
              <div class="event-card__status">
                <StatusTag :status="item.status" category="event" />
              </div>
              <div class="event-card__info">
                <div class="event-card__row">
                  <span class="event-card__icon">&#128197;</span>
                  <span>{{ formatTime(item.start_time) }}</span>
                </div>
                <div class="event-card__row">
                  <span class="event-card__icon">&#128205;</span>
                  <span>{{ item.location || '待定' }}</span>
                </div>
                <div class="event-card__row">
                  <span class="event-card__icon">&#128101;</span>
                  <span>{{ item.current_participants }} / {{ item.max_participants ?? '不限' }}</span>
                </div>
              </div>
              <div class="event-card__actions">
                <el-button size="small" @click="goDetail(item.id)">查看详情</el-button>
                <el-button
                  size="small"
                  type="primary"
                  :disabled="item.status === 'ended' || item.status === 'cancelled'"
                  @click="openRegisterDialog(item)"
                >
                  报名
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>
      <el-empty v-else description="暂无活动" style="margin-top: 60px" />

      <!-- 分页 -->
      <div v-if="total > 0" class="event-list__pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 报名弹窗 -->
    <el-dialog
      v-model="registerDialogVisible"
      :title="`报名活动：${registerEventName}`"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px" @submit.prevent="handleRegister">
        <el-form-item label="姓名" required>
          <el-input v-model="registerForm.customer_name" placeholder="请输入姓名" maxlength="30" />
        </el-form-item>
        <el-form-item label="联系方式" required>
          <el-input v-model="registerForm.contact_info" placeholder="手机号或邮箱" maxlength="50" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="registerForm.remark"
            type="textarea"
            :rows="3"
            placeholder="选填"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegister">
          确认报名
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.event-list {
  max-width: 1200px;
  margin: 0 auto;

  &__toolbar {
    background: #fff;
    padding: 16px 24px;
    border-bottom: 1px solid #ebeef5;
  }

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 24px;
    min-height: 200px;
  }

  &__pagination {
    margin-top: 24px;
    display: flex;
    justify-content: flex-end;
  }
}

.event-card {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  &__header {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }

  &__name {
    font-weight: 700;
    font-size: 15px;
    color: #303133;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 180px;
  }

  &__status {
    margin-bottom: 12px;
  }

  &__info {
    flex: 1;
    margin-bottom: 12px;
  }

  &__row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    font-size: 13px;
    color: #606266;
  }

  &__icon {
    margin-right: 6px;
  }

  &__actions {
    display: flex;
    justify-content: space-between;
    padding-top: 12px;
    border-top: 1px solid #ebeef5;
  }
}
</style>
