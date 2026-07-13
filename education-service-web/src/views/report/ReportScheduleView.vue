<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import PageHeader from '@/components/common/PageHeader.vue'

const BASE = '/api/v1/report/schedules'
const H = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })

/* ---------- 表格 ---------- */
const tableData = ref<any[]>([])
const loading = ref(false)

/* ---------- 获取调度列表 ---------- */
async function fetchSchedules() {
  loading.value = true
  try {
    const resp = await axios.get(BASE, { headers: H() })
    const res: any = resp.data
    // 兼容多种后端返回格式
    if (Array.isArray(res)) {
      tableData.value = res
    } else if (res?.items) {
      tableData.value = res.items
    } else if (res?.results) {
      tableData.value = res.results
    } else if (res?.schedules) {
      tableData.value = res.schedules
    } else {
      tableData.value = []
    }
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

/* ---------- 新增弹窗 ---------- */
const dialogVisible = ref(false)
const submitting = ref(false)
const createForm = reactive({
  name: '',
  cron_expression: '',
  report_type: '',
  enabled: true,
})

function openCreate() {
  createForm.name = ''
  createForm.cron_expression = ''
  createForm.report_type = ''
  createForm.enabled = true
  dialogVisible.value = true
}

async function submitCreate() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入调度名称')
    return
  }
  submitting.value = true
  try {
    await axios.post(BASE, {
      name: createForm.name,
      cron_expression: createForm.cron_expression,
      report_type: createForm.report_type,
      enabled: createForm.enabled,
    }, { headers: H() })
    ElMessage.success('调度创建成功')
    dialogVisible.value = false
    fetchSchedules()
  } catch {
    // 错误已在拦截器中统一处理
  } finally {
    submitting.value = false
  }
}

/* ---------- 删除调度 ---------- */
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除调度「${row.name || row.id}」吗？`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await axios.delete(`${BASE}/${row.id}`, { headers: H() })
    ElMessage.success('删除成功')
    fetchSchedules()
  } catch {
    // 用户取消 或 删除失败
  }
}

/* ---------- 格式化 ---------- */
function formatDate(val: string): string {
  if (!val) return '-'
  return val.slice(0, 10)
}

function formatTime(val: string): string {
  if (!val) return '-'
  const d = new Date(val)
  return d.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSchedules()
})
</script>

<template>
  <div class="report-schedule">
    <PageHeader>
      <template #actions>
        <el-button type="primary" @click="openCreate">新增调度</el-button>
      </template>
    </PageHeader>

    <div class="report-schedule__body" v-loading="loading">
      <el-table
        :data="tableData"
        border
        stripe
        style="width: 100%"
        empty-text="暂无调度"
      >
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="调度名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="cron_expression" label="Cron 表达式" min-width="140" show-overflow-tooltip />
        <el-table-column prop="report_type" label="报告类型" min-width="120" show-overflow-tooltip />
        <el-table-column label="启用状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下次执行" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.next_run_at) || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && tableData.length === 0" description="暂无调度" style="margin-top: 60px" />
    </div>

    <!-- 新增弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新增报告调度"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="调度名称" required>
          <el-input v-model="createForm.name" placeholder="如：每日日报" />
        </el-form-item>
        <el-form-item label="Cron 表达式">
          <el-input v-model="createForm.cron_expression" placeholder="如：0 0 8 * * ?（每天8点）" />
        </el-form-item>
        <el-form-item label="报告类型">
          <el-select v-model="createForm.report_type" placeholder="请选择报告类型" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="申请材料报告" value="application_material" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="createForm.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">
          确认创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.report-schedule {
  max-width: 1200px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    margin-top: 16px;
    min-height: 200px;
  }
}
</style>
