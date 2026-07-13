<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import request from '@/api/request'
import { crmApi } from '@/api/crm'
import PageHeader from '@/components/common/PageHeader.vue'

/* ---------- 角色判断 ---------- */
const auth = useAuthStore()
const isCustomer = auth.userType === 'customer'

/* ---------- echarts 动态导入,失败则降级 ---------- */
let echarts: any = null
const echartsReady = ref(false)

async function loadEcharts() {
  try {
    const mod = await import('echarts')
    echarts = mod
    echartsReady.value = true
  } catch {
    echartsReady.value = false
  }
}

const router = useRouter()

/* ---------- 近期活动 ---------- */
const events = ref<any[]>([])
const eventsLoading = ref(false)

async function fetchEvents() {
  eventsLoading.value = true
  try {
    const data: any = await request.get('/events', {
      params: { status: 'upcoming', page: 1, page_size: 5 },
    })
    if (Array.isArray(data)) {
      events.value = data
    } else if (data?.items) {
      events.value = data.items
    } else if (data?.results) {
      events.value = data.results
    } else {
      events.value = []
    }
  } catch {
    events.value = []
  } finally {
    eventsLoading.value = false
  }
}

/* ---------- 最新客户 ---------- */
const leads = ref<any[]>([])
const leadsLoading = ref(false)

const leadColumns = [
  { prop: 'customer_name', label: '客户姓名', minWidth: 100 },
  { prop: 'contact_info', label: '联系方式', minWidth: 130 },
  { prop: 'intended_country', label: '意向国家', minWidth: 100 },
  { prop: 'source_channel', label: '来源渠道', minWidth: 100 },
  { prop: 'status', label: '状态', minWidth: 80 },
]

async function fetchLeads() {
  leadsLoading.value = true
  try {
    const data: any = await crmApi.listLeads({ page: 1, page_size: 5 })
    if (data?.items) {
      leads.value = data.items
    } else if (Array.isArray(data)) {
      leads.value = data
    } else {
      leads.value = []
    }
  } catch {
    leads.value = []
  } finally {
    leadsLoading.value = false
  }
}

/* ---------- 图表数据 ---------- */
const allLeads = ref<any[]>([])
const chartLoading = ref(false)

/* 饼图: 客户状态分布 */
const pieRef = ref<HTMLDivElement | null>(null)
let pieChart: any = null
const statusCounts = ref<Record<string, number>>({})
const statusLabels: Record<string, string> = {
  new: '新客户',
  contacting: '联系中',
  qualified: '已甄别',
  signed: '已签约',
  lost: '已流失',
}

/* 柱状图: 近7天每日新增 */
const barRef = ref<HTMLDivElement | null>(null)
let barChart: any = null
const dailyCounts = ref<{ date: string; count: number }[]>([])

async function fetchAllLeads() {
  chartLoading.value = true
  try {
    const data: any = await crmApi.listLeads({ page: 1, page_size: 100 })
    let items: any[] = []
    if (data?.items) {
      items = data.items
    } else if (Array.isArray(data)) {
      items = data
    }
    allLeads.value = items

    /* 按 status 分组 */
    const counts: Record<string, number> = {}
    items.forEach((lead: any) => {
      const s = lead.status || 'unknown'
      counts[s] = (counts[s] || 0) + 1
    })
    statusCounts.value = counts

    /* 近7天每日新增 */
    const today = new Date()
    const dayMap: Record<string, number> = {}
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      dayMap[key] = 0
    }
    items.forEach((lead: any) => {
      const raw = lead.created_at || lead.create_time || lead.createTime
      if (raw) {
        const dateKey = raw.slice(0, 10)
        if (dayMap[dateKey] !== undefined) {
          dayMap[dateKey]++
        }
      }
    })
    const sorted = Object.entries(dayMap).map(([date, count]) => ({ date, count }))
    dailyCounts.value = sorted
  } catch {
    allLeads.value = []
    statusCounts.value = {}
    dailyCounts.value = []
  } finally {
    chartLoading.value = false
  }
}

/* ---------- 初始化图表 ---------- */
function initPieChart() {
  if (!echarts || !pieRef.value) return
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieRef.value)

  const data = Object.entries(statusCounts.value).map(([key, value]) => ({
    name: statusLabels[key] || key,
    value,
  }))

  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        data: data.length ? data : [{ name: '暂无数据', value: 1 }],
        label: { show: true, formatter: '{b}: {c}' },
      },
    ],
    color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
  })
}

function initBarChart() {
  if (!echarts || !barRef.value) return
  if (barChart) barChart.dispose()
  barChart = echarts.init(barRef.value)

  const xData = dailyCounts.value.map((d) => d.date.slice(5))
  const yData = dailyCounts.value.map((d) => d.count)

  barChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: xData },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: yData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#1a73e8' },
            { offset: 1, color: '#0d47a1' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
    grid: { left: 10, right: 10, top: 10, bottom: 40 },
  })
}

function renderCharts() {
  nextTick(() => {
    initPieChart()
    initBarChart()
  })
}

function handleResize() {
  pieChart?.resize()
  barChart?.resize()
}

/* ---------- 生命周期 ---------- */
onMounted(async () => {
  await loadEcharts()
  fetchEvents()
  if (!isCustomer) {
    fetchLeads()
    fetchAllLeads().then(() => {
      if (echartsReady.value) renderCharts()
    })
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  barChart?.dispose()
})

/* 数据加载完成后渲染图表 */
watch(allLeads, () => {
  if (echartsReady.value) renderCharts()
})

/* ---------- 工具函数 ---------- */
function formatEventDate(d: string): string {
  if (!d) return ''
  return d.slice(0, 10)
}

function truncate(text: string, len = 60): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function handleEventClick(event: any) {
  if (event.id) {
    router.push(`/events/${event.id}`)
  }
}

function handleLeadRowClick(row: any) {
  if (row.id) {
    router.push(`/crm/leads/${row.id}`)
  }
}

/* ---------- 统计值（硬编码占位，可后续接 API） ---------- */
const stats = [
  { label: '今日新增客户', value: 5, color: '#409eff', icon: 'User', trend: 12 },
  { label: '跟进中客户', value: 23, color: '#67c23a', icon: 'ChatDotRound', trend: 8 },
  { label: '近期活动', value: 3, color: '#e6a23c', icon: 'Calendar', trend: 0 },
  { label: '活动报名数', value: 47, color: '#7c3aed', icon: 'List', trend: -3 },
]
</script>

<template>
  <div class="dashboard">
    <PageHeader />

    <!-- 统计卡片 - 非 customer 角色显示 -->
    <el-row v-if="!isCustomer" :gutter="16" class="stats-row">
      <el-col v-for="(stat, idx) in stats" :key="idx" :xs="12" :sm="6">
        <div class="stat-card" :style="{ borderTopColor: stat.color }">
          <div class="stat-card__body">
            <div class="stat-card__icon" :style="{ background: stat.color }">
              <el-icon :size="20" color="#fff">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-card__info">
              <span class="stat-card__label">{{ stat.label }}</span>
              <span class="stat-card__value">{{ stat.value }}</span>
            </div>
          </div>
          <div class="stat-card__trend" v-if="stat.trend !== 0">
            <span :class="stat.trend > 0 ? 'trend-up' : 'trend-down'">
              {{ stat.trend > 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
            </span>
            <span class="trend-hint">较昨日</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 近期活动 -->
    <div class="dashboard__section" v-loading="eventsLoading">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon :size="18" color="#1a73e8"><Calendar /></el-icon>
          <span>近期活动</span>
        </h3>
      </div>
      <div v-if="events.length" class="events-grid">
        <div
          v-for="event in events"
          :key="event.id"
          class="event-card"
          @click="handleEventClick(event)"
        >
          <div class="event-card__cover">
            <el-icon :size="40" color="rgba(255,255,255,0.9)"><Picture /></el-icon>
          </div>
          <div class="event-card__body">
            <div class="event-card__header">
              <span class="event-card__name">{{ event.name || event.title || '未命名活动' }}</span>
              <el-tag size="small" type="success" effect="plain">即将开始</el-tag>
            </div>
            <p class="event-card__desc">
              {{ truncate(event.description || event.desc || '暂无描述') }}
            </p>
            <div class="event-card__meta">
              <span v-if="event.start_time || event.event_date">
                <el-icon :size="13"><Clock /></el-icon>
                {{ formatEventDate(event.start_time || event.event_date) }}
              </span>
              <span v-if="event.location">
                <el-icon :size="13"><Location /></el-icon>
                {{ event.location }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无近期活动" />
    </div>

    <!-- 数据概览 - 非 customer 角色显示 -->
    <div v-if="!isCustomer" class="dashboard__section" v-loading="chartLoading">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon :size="18" color="#1a73e8"><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </h3>
      </div>

      <!-- ECharts 图表模式 -->
      <div v-if="echartsReady" class="charts-row">
        <div class="chart-card" shadow="hover">
          <div class="chart-card__head">
            <el-icon :size="18" color="#409eff"><PieChart /></el-icon>
            <span>客户状态分布</span>
          </div>
          <div ref="pieRef" class="chart-box"></div>
        </div>
        <div class="chart-card" shadow="hover">
          <div class="chart-card__head">
            <el-icon :size="18" color="#1a73e8"><Histogram /></el-icon>
            <span>近7天新增客户</span>
          </div>
          <div ref="barRef" class="chart-box"></div>
        </div>
      </div>

      <!-- 降级模式: el-progress 百分比条 -->
      <div v-else class="charts-row">
        <div class="chart-card" shadow="hover">
          <div class="chart-card__head">
            <el-icon :size="18" color="#409eff"><PieChart /></el-icon>
            <span>客户状态分布</span>
          </div>
          <div v-if="Object.keys(statusCounts).length" class="progress-list">
            <div
              v-for="(count, status) in statusCounts"
              :key="status"
              class="progress-item"
            >
              <span class="progress-item__label">{{ statusLabels[status] || status }}</span>
              <el-progress
                :percentage="allLeads.length ? Math.round((count / allLeads.length) * 100) : 0"
                :stroke-width="16"
                style="flex: 1; margin: 0 12px"
              />
              <span class="progress-item__count">{{ count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </div>
        <div class="chart-card" shadow="hover">
          <div class="chart-card__head">
            <el-icon :size="18" color="#1a73e8"><Histogram /></el-icon>
            <span>近7天新增客户</span>
          </div>
          <div v-if="dailyCounts.length" class="progress-list">
            <div
              v-for="item in dailyCounts"
              :key="item.date"
              class="progress-item"
            >
              <span class="progress-item__label">{{ item.date.slice(5) }}</span>
              <el-progress
                :percentage="Math.max(...dailyCounts.map(d => d.count)) ? Math.round((item.count / (Math.max(...dailyCounts.map(d => d.count)) || 1)) * 100) : 0"
                :stroke-width="16"
                style="flex: 1; margin: 0 12px"
              />
              <span class="progress-item__count">{{ item.count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </div>
      </div>
    </div>

    <!-- 最新客户 - 非 customer 角色显示 -->
    <div v-if="!isCustomer" class="dashboard__section" v-loading="leadsLoading">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon :size="18" color="#1a73e8"><Avatar /></el-icon>
          <span>最新客户</span>
        </h3>
      </div>
      <el-table
        v-if="leads.length"
        :data="leads"
        stripe
        @row-click="handleLeadRowClick"
        class="leads-table"
        style="cursor: pointer"
      >
        <el-table-column
          v-for="col in leadColumns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.minWidth"
        />
        <el-table-column label="创建时间" min-width="120">
          <template #default="{ row }">
            {{ formatEventDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无客户数据" />
    </div>
  </div>
</template>

<script lang="ts">
import {
  User,
  ChatDotRound,
  Calendar,
  List,
  Clock,
  Location,
  Picture,
  PieChart,
  Histogram,
  DataAnalysis,
  Avatar,
} from '@element-plus/icons-vue'
export default {
  components: {
    User,
    ChatDotRound,
    Calendar,
    List,
    Clock,
    Location,
    Picture,
    PieChart,
    Histogram,
    DataAnalysis,
    Avatar,
  },
}
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 32px;

  &__section {
    margin-top: 24px;
    background: #fff;
    border-radius: 4px;
    padding: 20px;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  }
}

/* ========== 区块标题 ========== */
.section-header {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* ========== 统计卡片 ========== */
.stats-row {
  margin-top: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 4px;
  border-top: 4px solid;
  padding: 20px 16px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  }

  &__body {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  &__icon {
    width: 44px;
    height: 44px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__info {
    display: flex;
    flex-direction: column;
  }

  &__label {
    font-size: 13px;
    color: #909399;
    margin-bottom: 4px;
  }

  &__value {
    font-size: 32px;
    font-weight: 700;
    color: #1a1a2e;
    line-height: 1.1;
  }

  &__trend {
    margin-top: 12px;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.trend-up {
  color: #67c23a;
  font-weight: 600;
}

.trend-down {
  color: #f56c6c;
  font-weight: 600;
}

.trend-hint {
  color: #c0c4cc;
}

/* ========== 近期活动 ========== */
.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.event-card {
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  }

  &__cover {
    height: 100px;
    background: linear-gradient(135deg, #1a73e8, #0d47a1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__body {
    padding: 14px 16px;
  }

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  &__name {
    font-weight: 600;
    font-size: 14px;
    color: #1a1a2e;
  }

  &__desc {
    margin: 0 0 10px;
    font-size: 13px;
    color: #606266;
    line-height: 1.5;
  }

  &__meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: #909399;

    span {
      display: flex;
      align-items: center;
      gap: 3px;
    }
  }
}

/* ========== 图表区域 ========== */
.charts-row {
  display: flex;
  gap: 16px;
}

.chart-card {
  flex: 1;
  min-width: 0;
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);

  &__head {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 12px;
  }
}

.chart-box {
  width: 100%;
  height: 280px;
}

/* 降级进度条 */
.progress-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 0;
}

.progress-item {
  display: flex;
  align-items: center;

  &__label {
    width: 60px;
    font-size: 13px;
    color: #606266;
    flex-shrink: 0;
  }

  &__count {
    width: 32px;
    font-size: 13px;
    color: #303133;
    font-weight: 600;
    text-align: right;
    flex-shrink: 0;
  }
}

/* ========== 客户表格 ========== */
.leads-table {
  border-radius: 4px;
}
</style>
