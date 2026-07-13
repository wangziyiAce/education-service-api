<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { reportApi } from '@/api/report'
import PageHeader from '@/components/common/PageHeader.vue'

/* ---------- 日期选择 ---------- */
function todayStr(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const reportDate = ref(todayStr())
const loading = ref(false)

/* ---------- 汇总数据 ---------- */
interface TeamSubmission {
  total?: number
  submitted?: number
  unsubmitted?: number
}

interface KeyProgress {
  employee_name?: string
  progress?: string
}

interface SummaryData {
  report_date?: string
  team_submission?: TeamSubmission
  key_progress?: KeyProgress[]
  risks?: string[]
  ai_summary?: string
}

const summary = ref<SummaryData | null>(null)

async function fetchSummary() {
  if (!reportDate.value) return
  loading.value = true
  try {
    const data: any = await reportApi.getSummary(reportDate.value)
    summary.value = data
  } catch {
    summary.value = null
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  fetchSummary()
}

function hasData(): boolean {
  if (!summary.value) return false
  const s = summary.value
  return !!(
    s.team_submission ||
    (s.key_progress && s.key_progress.length > 0) ||
    (s.risks && s.risks.length > 0) ||
    s.ai_summary
  )
}

onMounted(() => {
  fetchSummary()
})
</script>

<template>
  <div class="report-detail">
    <PageHeader />

    <div class="report-detail__body" v-loading="loading">
      <!-- 日期选择器 -->
      <div class="report-detail__toolbar">
        <span class="report-detail__label">选择日期：</span>
        <el-date-picker
          v-model="reportDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          @change="handleDateChange"
        />
      </div>

      <!-- 汇总内容 -->
      <template v-if="summary && hasData()">
        <!-- 团队提交情况 -->
        <el-card v-if="summary.team_submission" class="section-card" shadow="never">
          <template #header>
            <span class="section-title">团队提交情况</span>
          </template>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-statistic
                title="团队总人数"
                :value="summary.team_submission.total ?? 0"
              />
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="已提交"
                :value="summary.team_submission.submitted ?? 0"
                value-style="color: #67c23a"
              />
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="未提交"
                :value="summary.team_submission.unsubmitted ?? 0"
                value-style="color: #f56c6c"
              />
            </el-col>
          </el-row>
        </el-card>

        <!-- 关键进展 -->
        <el-card
          v-if="summary.key_progress && summary.key_progress.length"
          class="section-card"
          shadow="never"
        >
          <template #header>
            <span class="section-title">每人关键进展</span>
          </template>
          <div
            v-for="(item, idx) in summary.key_progress"
            :key="idx"
            class="progress-item"
          >
            <span class="progress-item__name">{{ item.employee_name || '未知' }}</span>
            <span class="progress-item__text">{{ item.progress || '暂无进展' }}</span>
          </div>
        </el-card>

        <!-- 风险 -->
        <el-card
          v-if="summary.risks && summary.risks.length"
          class="section-card"
          shadow="never"
        >
          <template #header>
            <span class="section-title">风险提示</span>
          </template>
          <el-tag
            v-for="(risk, idx) in summary.risks"
            :key="idx"
            type="danger"
            effect="plain"
            class="risk-tag"
          >
            {{ risk }}
          </el-tag>
        </el-card>

        <!-- AI 总览 -->
        <el-card v-if="summary.ai_summary" class="section-card" shadow="never">
          <template #header>
            <span class="section-title">AI 总览分析</span>
          </template>
          <p class="ai-summary">{{ summary.ai_summary }}</p>
        </el-card>
      </template>

      <!-- 空状态 -->
      <el-empty
        v-else-if="!loading"
        description="暂无该日期的汇总数据"
        style="margin-top: 60px"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.report-detail {
  max-width: 1200px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    min-height: 400px;
  }

  &__toolbar {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  &__label {
    margin-right: 12px;
    font-weight: 500;
    color: #303133;
  }
}

.section-card {
  margin-bottom: 16px;

  :deep(.el-card__header) {
    background: #fafafa;
    padding: 12px 16px;
  }
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.progress-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;

  &:last-child {
    border-bottom: none;
  }

  &__name {
    min-width: 80px;
    font-weight: 600;
    color: #303133;
    flex-shrink: 0;
  }

  &__text {
    color: #606266;
    line-height: 1.6;
  }
}

.risk-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.ai-summary {
  margin: 0;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
