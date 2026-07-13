<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import PageHeader from '@/components/common/PageHeader.vue'

const BASE = '/api/v1/report/data'

/* ---------- 表格 ---------- */
const tableData = ref<any[]>([])
const loading = ref(false)

/* ---------- 分页 ---------- */
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

/* ---------- 获取数据 ---------- */
async function fetchData() {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await axios.get(`${BASE}/application-materials`, {
      params: { page: pagination.page, page_size: pagination.pageSize },
      headers: { Authorization: `Bearer ${token}` }
    })
    const res: any = resp.data
    // 兼容多种后端返回格式
    if (Array.isArray(res)) {
      tableData.value = res
      pagination.total = res.length
    } else if (res?.items) {
      tableData.value = res.items
      pagination.total = res.total || res.items.length
    } else if (res?.results) {
      tableData.value = res.results
      pagination.total = res.count || res.results.length
    } else {
      tableData.value = []
      pagination.total = 0
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
const createForm = reactive<Record<string, any>>({})

function openCreate() {
  Object.keys(createForm).forEach(key => delete createForm[key])
  dialogVisible.value = true
}

async function submitCreate() {
  submitting.value = true
  try {
    const token = localStorage.getItem('access_token')
    await axios.post(`${BASE}/application-materials`, createForm, {
      headers: { Authorization: `Bearer ${token}` }
    })
    ElMessage.success('新增成功')
    dialogVisible.value = false
    fetchData()
  } catch {
    // 错误已在拦截器中统一处理
  } finally {
    submitting.value = false
  }
}

/* ---------- 分页变化 ---------- */
function handlePageChange(page: number) {
  pagination.page = page
  fetchData()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

/* ---------- 动态列（从首行提取） ---------- */
function extractColumns(data: any[]): string[] {
  if (!data.length) return []
  const first = data[0]
  return Object.keys(first).filter(k => k !== 'id' && typeof first[k] !== 'object')
}

/* ---------- 单元格渲染 ---------- */
function formatCell(value: any): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  return String(value)
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="report-data">
    <PageHeader>
      <template #actions>
        <el-button type="primary" @click="openCreate">新增数据</el-button>
      </template>
    </PageHeader>

    <div class="report-data__body" v-loading="loading">
      <el-table
        :data="tableData"
        border
        stripe
        style="width: 100%"
        empty-text="暂无数据"
      >
        <el-table-column type="index" label="#" width="60" />
        <el-table-column
          v-for="col in extractColumns(tableData)"
          :key="col"
          :prop="col"
          :label="col"
          min-width="120"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ formatCell(row[col]) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="report-data__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>

      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" style="margin-top: 60px" />
    </div>

    <!-- 新增弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新增申请材料"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="材料名称">
          <el-input v-model="createForm.name" placeholder="请输入材料名称" />
        </el-form-item>
        <el-form-item label="材料类型">
          <el-input v-model="createForm.type" placeholder="如：成绩单、推荐信、个人陈述" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入材料描述"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="createForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="待提交" value="pending" />
            <el-option label="已提交" value="submitted" />
            <el-option label="审核中" value="reviewing" />
            <el-option label="已通过" value="approved" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">
          确认新增
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.report-data {
  max-width: 1200px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    margin-top: 16px;
    min-height: 200px;
  }

  &__pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
