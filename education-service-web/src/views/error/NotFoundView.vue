<script setup lang="ts">
</script>

<template>
  <el-result icon="error" title="404" sub-title="页面未找到">
    <template #extra>
      <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
    </template>
  </el-result>
</template>
