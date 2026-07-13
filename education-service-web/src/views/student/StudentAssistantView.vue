<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/api/request'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const auth = useAuthStore()

const studentId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const scrollbarRef = ref<any>(null)

onMounted(() => {
  // auth.user 中 id 字段可能是 id 或 user_id（取决于 login 映射还是 restoreFromToken）
  const uid = (auth.user as any)?.id ?? (auth.user as any)?.user_id
  if (uid) {
    studentId.value = uid
  }
})

function scrollToBottom() {
  nextTick(() => {
    const wrap = scrollbarRef.value?.wrapRef
    if (wrap) {
      wrap.scrollTop = wrap.scrollHeight
    }
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || studentId.value === null || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const reply = await request.post('/student/chat', null, {
      params: { student_id: studentId.value, message: text },
    })
    messages.value.push({ role: 'assistant', content: reply as unknown as string })
  } catch {
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。' })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="student-assistant">
    <PageHeader />
    <div v-if="studentId !== null" class="student-assistant__info">
      当前学生ID: {{ studentId }}
    </div>
    <div v-else class="student-assistant__info student-assistant__info--warn">
      未获取到学生ID，请确认登录状态
    </div>

    <div class="student-assistant__chat">
      <!-- 消息区 -->
      <el-scrollbar ref="scrollbarRef" class="student-assistant__messages">
        <div v-if="messages.length === 0" class="student-assistant__empty">
          有什么可以帮你的？
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="student-assistant__bubble-row"
          :class="msg.role === 'user' ? 'student-assistant__bubble-row--user' : 'student-assistant__bubble-row--assistant'"
        >
          <div
            class="student-assistant__bubble"
            :class="msg.role === 'user' ? 'student-assistant__bubble--user' : 'student-assistant__bubble--assistant'"
          >
            {{ msg.content }}
          </div>
        </div>
      </el-scrollbar>

      <!-- 输入区 -->
      <div class="student-assistant__input-area">
        <el-input
          v-model="inputText"
          placeholder="输入消息，按 Enter 发送"
          :disabled="sending || studentId === null"
          @keydown="handleKeydown"
          class="student-assistant__input"
        />
        <el-button
          type="primary"
          :disabled="!inputText.trim() || sending || studentId === null"
          :loading="sending"
          @click="sendMessage"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.student-assistant {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;

  &__info {
    padding: 8px 24px;
    font-size: 13px;
    color: #909399;
    background: #fff;
    border-bottom: 1px solid #ebeef5;

    &--warn {
      color: #e6a23c;
    }
  }

  &__chat {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  &__messages {
    flex: 1;
    padding: 16px 24px;
  }

  &__empty {
    text-align: center;
    color: #c0c4cc;
    margin-top: 80px;
    font-size: 15px;
  }

  &__bubble-row {
    display: flex;
    margin-bottom: 16px;

    &--user {
      justify-content: flex-end;
    }

    &--assistant {
      justify-content: flex-start;
    }
  }

  &__bubble {
    max-width: 70%;
    padding: 10px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;

    &--user {
      background: #409eff;
      color: #fff;
      border-bottom-right-radius: 4px;
    }

    &--assistant {
      background: #f0f0f0;
      color: #303133;
      border-bottom-left-radius: 4px;
    }
  }

  &__input-area {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 24px;
    background: #fff;
    border-top: 1px solid #ebeef5;
  }

  &__input {
    flex: 1;
    :deep(.el-input__wrapper) {
      border-radius: 20px;
    }
  }
}
</style>
