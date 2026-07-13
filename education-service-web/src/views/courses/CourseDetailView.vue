<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api/chat'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { Course } from '@/types/chat'

const route = useRoute()
const router = useRouter()

const courseId = Number(route.params.id)
const course = ref<Course | null>(null)
const loading = ref(false)

function getStatusString(status: number): string {
  return String(status)
}

async function fetchCourse() {
  loading.value = true
  try {
    course.value = await chatApi.getCourse(courseId)
  } catch {
    ElMessage.error('获取课程详情失败')
  } finally {
    loading.value = false
  }
}

function handleBack() {
  router.push('/courses')
}

onMounted(() => {
  fetchCourse()
})
</script>

<template>
  <div class="course-detail">
    <PageHeader>
      <template #actions>
        <el-button @click="handleBack">返回列表</el-button>
      </template>
    </PageHeader>

    <div
      class="course-detail__body"
      v-if="course"
      v-loading="loading"
    >
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <StatusTag :status="getStatusString(course.status)" category="course" size="default" />
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="课程 ID">{{ course.id }}</el-descriptions-item>
          <el-descriptions-item label="课程名称">{{ course.project_name }}</el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ course.category || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="价格">
            {{ course.price ? `¥${course.price}` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="周期">
            {{ course.duration || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="适合人群">
            {{ course.target_audience || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <template v-if="course.tags && course.tags.length">
              <el-tag
                v-for="(tag, idx) in course.tags"
                :key="idx"
                size="small"
                style="margin-right: 6px"
              >
                {{ tag }}
              </el-tag>
            </template>
            <template v-else>-</template>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ course.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ course.create_time }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.course-detail {
  max-width: 900px;
  margin: 0 auto;
  &__body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }
}
.info-card {
  border-radius: 4px;
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
