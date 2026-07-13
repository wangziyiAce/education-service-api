<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pageTitle = computed(() => route.meta?.title as string || '')
</script>

<template>
  <div class="page-header">
    <div class="page-header__left">
      <h2 class="page-header__title">{{ pageTitle }}</h2>
    </div>
    <div class="page-header__right">
      <slot name="actions" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  &__title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }
}
</style>
