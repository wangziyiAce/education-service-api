<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { studentApi } from '@/api/student'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { PsychAlert } from '@/types/student'

const auth = useAuthStore()

const riskLevelOptions = [
  { label: '全部', value: '' },
  { label: '低风险', value: 'low' },
  { label: '中风险', value: 'medium' },
  { label: '高风险', value: 'high' },
]

const alertStatusMap: Record<string, { label: string; color: string }> = {
  pending:   { label: '待处理', color: 'warning' },
  following: { label: '跟进中', color: 'primary' },
  resolved:  { label: '已解决', color: 'success' },
  dismissed: { label: '已驳回', color: 'info' },
}

const statusTagColorMap: Record<string, string> = {
  warning: 'warning',
  primary: '',
  success: 'success',
  info: 'info',
  danger: 'danger',
}

const filterRiskLevel = ref('')
const loading = ref(false)
const list = ref<PsychAlert[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

/* ---------- 处理弹窗 ---------- */
const dialogVisible = ref(false)
const currentRow = ref<PsychAlert | null>(null)
const processForm = reactive({
  status: 'following' as string,
  handler_comment: '',
})
const submitting = ref(false)

function getRiskLevelLabel(level: string) {
  const found = riskLevelOptions.find((o) => o.value === level)
  return found ? found.label : level
}

function getAlertStatusConfig(status: string) {
  return alertStatusMap[status] || { label: status, color: 'info' }
}

/* ---------- 数据加载 ---------- */
async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filterRiskLevel.value) params.risk_level = filterRiskLevel.value
    const res = await studentApi.listPsychAlerts(params)
    list.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('加载心理预警列表失败')
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  page.value = 1
  fetchData()
}

function handlePageChange(p: number) {
  page.value = p
  fetchData()
}

/* ---------- 处理弹窗逻辑 ---------- */
function openProcessDialog(row: PsychAlert) {
  currentRow.value = row
  processForm.status = 'following'
  processForm.handler_comment = ''
  dialogVisible.value = true
}

async function handleProcess() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await studentApi.handlePsychAlert(currentRow.value.id, {
      status: processForm.status,
      handler_id: auth.user!.id,
      handler_comment: processForm.handler_comment || undefined,
    })
    ElMessage.success('处理完成')
    dialogVisible.value = false
    fetchData()
  } catch {
    ElMessage.error('处理失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="psych-alert-list">
    <PageHeader />
    <div class="psych-alert-list__body">
      <!-- 筛选栏 -->
      <div class="psych-alert-list__filter">
        <span class="psych-alert-list__filter-label">风险等级：</span>
        <el-select
          v-model="filterRiskLevel"
          placeholder="全部"
          style="width: 140px"
          @change="handleFilterChange"
        >
          <el-option
            v-for="opt in riskLevelOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <!-- 表格 -->
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="学生姓名" min-width="100">
          <template #default="{ row }">
            {{ row.student_name || String(row.student_id) }}
          </template>
        </el-table-column>
        <el-table-column label="风险等级" min-width="90">
          <template #default="{ row }">
            <StatusTag :status="row.risk_level" category="psych" />
          </template>
        </el-table-column>
        <el-table-column label="触发原因" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.trigger_reason || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="状态" min-width="90">
          <template #default="{ row }">
            <el-tag
              :type="getAlertStatusConfig(row.status).color as any"
              size="small"
            >
              {{ getAlertStatusConfig(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              size="small"
              @click="openProcessDialog(row)"
            >
              处理
            </el-button>
            <span v-else class="psych-alert-list__no-action">--</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="psych-alert-list__pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 处理弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="处理心理预警"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px">
        <el-form-item label="学生姓名">
          <span>{{ currentRow?.student_name || currentRow?.student_id || '--' }}</span>
        </el-form-item>
        <el-form-item label="风险等级">
          <StatusTag
            v-if="currentRow"
            :status="currentRow.risk_level"
            category="psych"
          />
        </el-form-item>
        <el-form-item label="触发原因">
          <div class="psych-alert-list__reason">
            {{ currentRow?.trigger_reason || '--' }}
          </div>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="processForm.status" style="width: 100%">
            <el-option label="待处理" value="pending" />
            <el-option label="跟进中" value="following" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已驳回" value="dismissed" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理记录">
          <el-input
            v-model="processForm.handler_comment"
            type="textarea"
            :rows="4"
            placeholder="请输入处理记录（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleProcess">确 认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.psych-alert-list {
  max-width: 1200px;
  margin: 0 auto;
  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
  }
  &__filter {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  &__filter-label {
    font-size: 14px;
    color: #606266;
    margin-right: 8px;
  }
  &__pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
  &__reason {
    color: #303133;
    line-height: 1.6;
    max-height: 120px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
  &__no-action {
    color: #c0c4cc;
  }
}
</style>
