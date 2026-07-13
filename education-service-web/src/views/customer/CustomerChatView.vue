<script setup lang="ts">
import { onMounted } from 'vue'

const difyUrl = 'http://localhost/chat/dV0QCIXO8Uokr1Bh'

onMounted(() => {
  // 直接跳转到 Dify WebApp，避免 iframe 跨域导致 cookie/session 丢失
  window.location.href = difyUrl
})
</script>

<template>
  <div class="customer-chat">
    <div class="customer-chat__body">
      <el-result icon="success" title="正在跳转到智能客服...">
        <template #extra>
          <a :href="difyUrl">
            <el-button type="primary" size="large">如未跳转，点击这里</el-button>
          </a>
        </template>
      </el-result>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.customer-chat {
  height: 100%;
  display: flex;
  &__body {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
