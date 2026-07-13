<script setup lang="ts">
import { computed } from 'vue'
import { STATUS_MAP } from '@/utils/constants'

const props = defineProps<{
  status: string
  category: 'lead' | 'event' | 'leave' | 'feedback' | 'psych' | 'report' | 'course'
  size?: 'small' | 'default' | 'large'
}>()

const config = computed(() => {
  return STATUS_MAP[props.category]?.[props.status] || { label: props.status, color: 'info' }
})
</script>

<template>
  <el-tag :type="config.color as any" :size="size || 'small'">
    {{ config.label }}
  </el-tag>
</template>
