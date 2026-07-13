<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { studentApi } from '@/api/student'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { FeedbackTicket } from '@/types/student'

const auth = useAuthStore()

const tabs = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' },
]

const ticketTypeMap: Record<string, string> = {
  complaint: '投诉',
  suggestion: '建议',
  consult: '咨询',
}

const activeTab = ref('')
const loading = ref(false)
const list = ref<FeedbackTicket[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 处理弹窗
const dialogVisible = ref(false)
const currentRow = ref<FeedbackTicket | null>(null)
const processForm = reactive({
  status: 'processing' as string,
  handler_comment: '',
})
const submitting = ref(false)

function getTicketTypeLabel(type: string) {
  return ticketTypeMap[type] || type
}

function getStudentDisplay(row: FeedbackTicket) {
  return row.student_name || String(row.student_id)
}

function truncateContent(content: string, maxLen = 30) {
  if (!content) return ''
  return content.length > maxLen ? content.slice(0, maxLen) + '...' : content
}

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (activeTab.value) params.status = activeTab.value
    const res = await studentApi.listAllFeedbacks(params)
    list.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('加载投诉列表失败')
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

function openProcessDialog(row: FeedbackTicket) {
  currentRow.value = row
  processForm.status = 'processing'
  processForm.handler_comment = ''
  dialogVisible.value = true
}

async function handleProcess() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await studentApi.updateFeedback(currentRow.value.id, {
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
  <div class="feedback-list">
    <PageHeader />
    <div class="feedback-list__body">
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
        <el-table-column label="类型" min-width="80">
          <template #default="{ row }">
            {{ getTicketTypeLabel(row.ticket_type) }}
          </template>
        </el-table-column>
        <el-table-column label="内容" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ truncateContent(row.content) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="80">
          <template #default="{ row }">
            <StatusTag :status="row.status" category="feedback" />
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'resolved'"
              type="primary"
              size="small"
              @click="openProcessDialog(row)"
            >
              处理
            </el-button>
            <span v-else class="feedback-list__no-action">--</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="feedback-list__pagination">
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
      title="处理投诉"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px">
        <el-form-item label="学生">
          <span>{{ currentRow ? getStudentDisplay(currentRow) : '' }}</span>
        </el-form-item>
        <el-form-item label="类型">
          <span>{{ currentRow ? getTicketTypeLabel(currentRow.ticket_type) : '' }}</span>
        </el-form-item>
        <el-form-item label="内容">
          <span>{{ currentRow?.content || '--' }}</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="processForm.status" style="width: 100%">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理意见">
          <el-input
            v-model="processForm.handler_comment"
            type="textarea"
            :rows="3"
            placeholder="请输入处理意见（选填）"
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
.feedback-list {
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
