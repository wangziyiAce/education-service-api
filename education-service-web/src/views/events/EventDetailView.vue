<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatApi } from '@/api/chat'
import type { Event } from '@/types/chat'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const route = useRoute()
const router = useRouter()

const event = ref<Event | null>(null)
const loading = ref(false)

const typeLabelMap: Record<string, string> = {
  online: '线上',
  offline: '线下',
  hybrid: '混合',
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function goBack() {
  router.push('/events')
}

async function fetchEvent() {
  const id = Number(route.params.id)
  if (!id) {
    router.replace('/events')
    return
  }
  loading.value = true
  try {
    event.value = await chatApi.getEvent(id)
  } catch {
    // 错误已在 request 拦截器中统一处理
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchEvent()
})
</script>

<template>
  <div class="event-detail">
    <PageHeader>
      <template #actions>
        <el-button @click="goBack">返回列表</el-button>
      </template>
    </PageHeader>

    <div class="event-detail__body" v-loading="loading">
      <template v-if="event">
        <el-descriptions :column="2" border size="large" title="活动详情">
          <el-descriptions-item label="活动名称" :span="2">
            <strong>{{ event.event_name }}</strong>
          </el-descriptions-item>
          <el-descriptions-item label="活动类型">
            <el-tag size="small" type="info">
              {{ typeLabelMap[event.event_type] || event.event_type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="event.status" category="event" />
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatTime(event.start_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ event.end_time ? formatTime(event.end_time) : '待定' }}
          </el-descriptions-item>
          <el-descriptions-item label="活动地点">
            {{ event.location || '待定' }}
          </el-descriptions-item>
          <el-descriptions-item label="名额">
            {{ event.max_participants ?? '不限' }}
          </el-descriptions-item>
          <el-descriptions-item label="已报名人数">
            {{ event.current_participants }}
          </el-descriptions-item>
          <el-descriptions-item label="剩余名额">
            {{ event.max_participants ? Math.max(0, event.max_participants - event.current_participants) : '不限' }}
          </el-descriptions-item>
          <el-descriptions-item label="活动描述" :span="2">
            <div style="white-space: pre-wrap; line-height: 1.6">
              {{ event.description || '暂无描述' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <el-empty v-else-if="!loading" description="活动不存在" style="margin-top: 60px" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.event-detail {
  max-width: 900px;
  margin: 0 auto;

  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 24px;
    min-height: 200px;
  }
}
</style>
