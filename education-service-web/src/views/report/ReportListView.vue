<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { reportApi } from '@/api/report'
import axios from 'axios'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()

/* ---------- 口述日报弹窗 ---------- */
const dialogVisible = ref(false)
const submitting = ref(false)

function todayStr(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const dictateForm = reactive({
  raw_content: '',
  report_date: todayStr(),
})

function openDictate() {
  dictateForm.raw_content = ''
  dictateForm.report_date = todayStr()
  dialogVisible.value = true
}

async function submitDictate() {
  if (!dictateForm.raw_content.trim()) {
    ElMessage.warning('请输入口述内容')
    return
  }
  submitting.value = true
  try {
    await reportApi.dictate({
      raw_content: dictateForm.raw_content,
      report_date: dictateForm.report_date,
    })
    ElMessage.success('日报提交成功')
    dialogVisible.value = false
    fetchReports()
  } catch {
    // 错误已在拦截器中统一处理
  } finally {
    submitting.value = false
  }
}

/* ---------- 查看日报汇总 ---------- */
function goToDetail() {
  router.push('/reports/detail')
}

/* ---------- 日报列表 ---------- */
const reports = ref<any[]>([])
const loading = ref(false)

async function fetchReports() {
  loading.value = true
  try {
    const data: any = await reportApi.listReports({
      employee_id: undefined,
      start_date: undefined,
      end_date: undefined,
    })
    // 兼容多种后端返回格式
    if (Array.isArray(data)) {
      reports.value = data
    } else if (data?.items) {
      reports.value = data.items
    } else if (data?.results) {
      reports.value = data.results
    } else {
      reports.value = []
    }
  } catch {
    reports.value = []
  } finally {
    loading.value = false
  }
}

function truncate(text: string, len = 80): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '…' : text
}

function formatDate(d: string): string {
  if (!d) return ''
  return d.slice(0, 10)
}

function statusColor(status: string): string {
  const map: Record<string, string> = {
    submitted: '#67c23a',
    pending: '#e6a23c',
    draft: '#909399',
  }
  return map[status] || '#909399'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    submitted: '已提交',
    pending: '待提交',
    draft: '草稿',
  }
  return map[status] || status || '未知'
}

/* ---------- 智能报告列表 ---------- */
const generations = ref<any[]>([])
const genLoading = ref(false)

async function fetchGenerations() {
  genLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await axios.get('/api/v1/report/generations', { headers: { Authorization: `Bearer ${token}` } })
    const data = resp.data?.data || resp.data
    generations.value = Array.isArray(data) ? data : (data?.items || [])
  } catch {
    generations.value = []
  } finally {
    genLoading.value = false
  }
}

function goGeneration(id: number) {
  router.push(`/reports/${id}`)
}

onMounted(() => {
  fetchReports()
  fetchGenerations()
})
</script>

<template>
  <div class="report-list">
    <PageHeader>
      <template #actions>
        <el-button type="primary" @click="openDictate">口述日报</el-button>
        <el-button @click="goToDetail">查看日报汇总</el-button>
        <el-button @click="router.push('/reports/assistant')">报告助手</el-button>
        <el-button @click="router.push('/reports/data')">报告数据</el-button>
        <el-button @click="router.push('/reports/schedules')">报告调度</el-button>
      </template>
    </PageHeader>

    <!-- 日报卡片列表 -->
    <div class="report-list__body" v-loading="loading">
      <template v-if="reports.length">
        <el-card
          v-for="item in reports"
          :key="item.id"
          class="report-card"
          shadow="hover"
        >
          <div class="report-card__header">
            <span class="report-card__date">{{ formatDate(item.report_date || item.created_at) }}</span>
            <el-tag
              :color="statusColor(item.status)"
              size="small"
              effect="dark"
            >
              {{ statusLabel(item.status) }}
            </el-tag>
          </div>
          <p class="report-card__summary">
            {{ truncate(item.content_summary || item.raw_content || '暂无内容') }}
          </p>
          <div v-if="item.employee_name" class="report-card__author">
            提交人：{{ item.employee_name }}
          </div>
        </el-card>
      </template>
      <el-empty v-else description="暂无日报记录" style="margin-top: 60px" />
    </div>

    <!-- 智能报告列表 -->
    <h3 style="margin: 24px 0 12px; font-size: 16px; color: #303133">智能报告</h3>
    <div class="report-list__body" v-loading="genLoading">
      <template v-if="generations.length">
        <el-card v-for="g in generations" :key="g.id" class="report-card" shadow="hover" @click="goGeneration(g.id)" style="cursor:pointer">
          <div class="report-card__header">
            <span class="report-card__date">{{ g.report_title || ('报告#' + g.id) }}</span>
            <el-tag :type="g.status === 'completed' ? 'success' : 'warning'" size="small">{{ g.status === 'completed' ? '已完成' : g.status }}</el-tag>
          </div>
          <p class="report-card__summary">{{ g.period_start || '?' }} ~ {{ g.period_end || '?' }} | 类型: {{ g.report_type }}</p>
        </el-card>
      </template>
      <el-empty v-else description="暂无智能报告" style="margin-top: 60px" />
    </div>

    <!-- 口述日报弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="口述日报"
      width="560px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="日报日期">
          <el-date-picker
            v-model="dictateForm.report_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="口述内容">
          <el-input
            v-model="dictateForm.raw_content"
            type="textarea"
            :rows="6"
            placeholder="请输入今天的工作内容、进展、遇到的问题等…"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitDictate">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.report-list {
  max-width: 1200px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    min-height: 200px;
  }
}

.report-card {
  margin-bottom: 12px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  &__date {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }

  &__summary {
    margin: 0 0 8px;
    color: #606266;
    line-height: 1.6;
  }

  &__author {
    font-size: 12px;
    color: #909399;
  }
}
</style>
