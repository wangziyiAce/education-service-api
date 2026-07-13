<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { chatApi } from '@/api/chat'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { Course } from '@/types/chat'

const router = useRouter()

const CATEGORY_OPTIONS = [
  { label: '全部', value: '' },
  { label: '语言培训', value: '语言培训' },
  { label: '背景提升', value: '背景提升' },
  { label: '留学申请', value: '留学申请' },
]

const searchForm = reactive({
  category: '',
  keyword: '',
  min_price: '',
  max_price: '',
})

const loading = ref(false)
const list = ref<Course[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const columns = [
  { prop: 'id', label: 'ID', width: 80 },
  { prop: 'project_name', label: '课程名称', minWidth: 180 },
  { prop: 'category', label: '分类', width: 100 },
  { prop: 'price', label: '价格', width: 100 },
  { prop: 'duration', label: '周期', width: 100 },
  { prop: 'target_audience', label: '适合人群', minWidth: 120 },
]

async function fetchCourses() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      status: 1,
    }
    if (searchForm.category) params.category = searchForm.category
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.min_price) params.min_price = searchForm.min_price
    if (searchForm.max_price) params.max_price = searchForm.max_price

    const data = await chatApi.listCourses(params)
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchCourses()
}

function handleReset() {
  searchForm.category = ''
  searchForm.keyword = ''
  searchForm.min_price = ''
  searchForm.max_price = ''
  currentPage.value = 1
  fetchCourses()
}

function handleRowClick(row: Course) {
  router.push(`/courses/${row.id}`)
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchCourses()
}

function getStatusString(status: number): string {
  return String(status)
}

onMounted(() => {
  fetchCourses()
})
</script>

<template>
  <div class="course-list">
    <PageHeader />

    <div class="course-list__body">
      <!-- 搜索栏 -->
      <el-card class="search-card" shadow="never">
        <el-form :inline="true" :model="searchForm" size="default">
          <el-form-item label="分类">
            <el-select v-model="searchForm.category" placeholder="全部分类" clearable style="width: 140px">
              <el-option
                v-for="opt in CATEGORY_OPTIONS"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="课程名称"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="价格区间">
            <el-input
              v-model="searchForm.min_price"
              placeholder="最低价"
              clearable
              style="width: 120px"
            />
            <span style="margin: 0 8px; color: #909399">-</span>
            <el-input
              v-model="searchForm.max_price"
              placeholder="最高价"
              clearable
              style="width: 120px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 表格 -->
      <el-card class="table-card" shadow="never">
        <el-table
          :data="list"
          v-loading="loading"
          stripe
          @row-click="handleRowClick"
          style="cursor: pointer"
        >
          <el-table-column
            v-for="col in columns"
            :key="col.prop"
            :prop="col.prop"
            :label="col.label"
            :width="col.width"
            :min-width="col.minWidth"
          >
            <template #default="{ row }">
              <template v-if="col.prop === 'price'">
                {{ row.price ? `¥${row.price}` : '-' }}
              </template>
              <template v-else-if="col.prop === 'duration'">
                {{ row.duration || '-' }}
              </template>
              <template v-else-if="col.prop === 'target_audience'">
                {{ row.target_audience || '-' }}
              </template>
              <template v-else-if="col.prop === 'category'">
                {{ row.category || '-' }}
              </template>
              <template v-else>
                {{ row[col.prop] }}
              </template>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <StatusTag :status="getStatusString(row.status)" category="course" />
            </template>
          </el-table-column>
        </el-table>

        <div class="course-list__pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.course-list {
  max-width: 1200px;
  margin: 0 auto;
  &__body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }
  &__pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
.search-card,
.table-card {
  border-radius: 4px;
}
</style>
