<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { studentApi } from '@/api/student'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { LeaveRecord } from '@/types/student'

const auth = useAuthStore()

const tabs = [
  { label: '全部', value: '' },
  { label: '待审批', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已驳回', value: 'rejected' },
]

const leaveTypeMap: Record<string, string> = {
  sick: '病假',
  personal: '事假',
  emergency: '紧急',
}

const activeTab = ref('')
const loading = ref(false)
const list = ref<LeaveRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 审批弹窗
const dialogVisible = ref(false)
const currentRow = ref<LeaveRecord | null>(null)
const approveForm = reactive({
  status: 'approved' as 'approved' | 'rejected',
  comment: '',
})
const submitting = ref(false)

function getLeaveTypeLabel(type: string) {
  return leaveTypeMap[type] || type
}

function getStudentDisplay(row: LeaveRecord) {
  return row.student_name || String(row.student_id)
}

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (activeTab.value) params.status = activeTab.value
    const res = await studentApi.listAllLeaves(params)
    list.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('加载请假列表失败')
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  page.value = 1
  fetchData()
}

function handlePageChange(p: number) {
  page.value = p
  fetchData()
}

function openApproveDialog(row: LeaveRecord) {
  currentRow.value = row
  approveForm.status = 'approved'
  approveForm.comment = ''
  dialogVisible.value = true
}

async function handleApprove() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await studentApi.approveLeave(currentRow.value.id, {
      approver_id: auth.user!.id,
      status: approveForm.status,
      comment: approveForm.comment || undefined,
    })
    ElMessage.success('审批完成')
    dialogVisible.value = false
    fetchData()
  } catch {
    ElMessage.error('审批失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="leave-list">
    <PageHeader />
    <div class="leave-list__body">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.value"
          :label="tab.label"
          :name="tab.value"
        />
      </el-tabs>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="学生姓名" min-width="100">
          <template #default="{ row }">
            {{ getStudentDisplay(row) }}
          </template>
        </el-table-column>
        <el-table-column label="请假类型" min-width="90">
          <template #default="{ row }">
            {{ getLeaveTypeLabel(row.leave_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="160" show-overflow-tooltip />
        <el-table-column prop="start_date" label="开始日期" min-width="110" />
        <el-table-column prop="end_date" label="结束日期" min-width="110" />
        <el-table-column label="状态" min-width="80">
          <template #default="{ row }">
            <StatusTag :status="row.status" category="leave" />
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              size="small"
              @click="openApproveDialog(row)"
            >
              审批
            </el-button>
            <span v-else class="leave-list__no-action">--</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="leave-list__pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 审批弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="审批请假"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px">
        <el-form-item label="学生">
          <span>{{ currentRow ? getStudentDisplay(currentRow) : '' }}</span>
        </el-form-item>
        <el-form-item label="请假类型">
          <span>{{ currentRow ? getLeaveTypeLabel(currentRow.leave_type) : '' }}</span>
        </el-form-item>
        <el-form-item label="原因">
          <span>{{ currentRow?.reason || '--' }}</span>
        </el-form-item>
        <el-form-item label="审批结果">
          <el-radio-group v-model="approveForm.status">
            <el-radio value="approved">通过</el-radio>
            <el-radio value="rejected">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input
            v-model="approveForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入审批意见（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleApprove">确 认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.leave-list {
  max-width: 1200px;
  margin: 0 auto;
  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
  }
  &__pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
  &__no-action {
    color: #c0c4cc;
  }
}
</style>
