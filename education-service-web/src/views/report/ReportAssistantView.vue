<script setup lang="ts">
import { ref, nextTick } from 'vue'
import axios from 'axios'
import PageHeader from '@/components/common/PageHeader.vue'

/* ---------- 消息列表 ---------- */
interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  needsClarification?: boolean
  intent?: string
  createTime: string
}

const messages = ref<ChatMessage[]>([])
const sending = ref(false)

/* ---------- 输入 ---------- */
const inputMessage = ref('')
const messagesContainer = ref<HTMLDivElement | null>(null)

/* ---------- 提示词 ---------- */
const hints = [
  '请帮我生成一份留学申请报告',
  '需要准备哪些申请材料？',
  '帮我分析一下当前的申请进度',
  '我的申请有哪些需要改进的地方？',
]

/* ---------- 发送消息 ---------- */
async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || sending.value) return

  inputMessage.value = ''
  sending.value = true

  // 添加用户消息
  const userMsg: ChatMessage = {
    id: Date.now(),
    role: 'user',
    content: text,
    createTime: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const resp = await axios.post('/api/v1/report/assistant/messages', { message: text }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const res: any = resp.data

    // 构建助手消息
    const assistantMsg: ChatMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: res?.answer || res?.reply_text || res?.content || '',
      needsClarification: !!res?.needs_clarification,
      intent: res?.intent,
      createTime: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)
    scrollToBottom()
  } catch {
    // 发送失败，移除临时用户消息
    messages.value = messages.value.filter(m => m.id !== userMsg.id)
  } finally {
    sending.value = false
  }
}

/* ---------- 回车发送 ---------- */
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

/* ---------- 滚动到底部 ---------- */
function scrollToBottom() {
  nextTick(() => {
    const el = messagesContainer.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

/* ---------- 格式化时间 ---------- */
function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <div class="report-assistant">
    <PageHeader>
      <template #actions>
        <span style="color: #909399; font-size: 13px">智能报告助手</span>
      </template>
    </PageHeader>

    <div class="report-assistant__body">
      <!-- 消息区（无侧边栏，单会话） -->
      <main class="chat-main">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="chat-main__empty">
          <el-icon :size="64" color="#dcdfe6"><ChatDotRound /></el-icon>
          <p style="color: #909399; margin-top: 16px">我是你的智能报告助手，可以帮你生成和分析各类报告</p>
          <div class="chat-main__hints">
            <span class="chat-main__hints-label">试试这些：</span>
            <el-tag
              v-for="h in hints"
              :key="h"
              class="chat-main__hint-tag"
              @click="inputMessage = h; sendMessage()"
            >
              {{ h }}
            </el-tag>
          </div>
        </div>

        <!-- 消息列表 -->
        <div
          v-if="messages.length > 0"
          ref="messagesContainer"
          class="chat-main__messages"
        >
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-row"
            :class="{ 'message-row--self': msg.role === 'user' }"
          >
            <!-- 助手头像 -->
            <div v-if="msg.role === 'assistant'" class="message-avatar">
              <el-avatar :size="36" icon="Service" />
            </div>

            <div class="message-bubble-wrapper">
              <div
                class="message-bubble"
                :class="{
                  'message-bubble--user': msg.role === 'user',
                  'message-bubble--assistant': msg.role === 'assistant',
                }"
              >
                <div class="message-bubble__text">{{ msg.content }}</div>
                <!-- 需要补充信息提示 -->
                <div v-if="msg.needsClarification" class="message-bubble__hint">
                  <el-alert
                    title="请补充更多信息"
                    type="warning"
                    :closable="false"
                    show-icon
                    style="margin-top: 8px"
                  />
                </div>
                <!-- 意图标签 -->
                <div v-if="msg.intent" class="message-bubble__intent">
                  <el-tag size="small" type="info">{{ msg.intent }}</el-tag>
                </div>
              </div>
              <div class="message-bubble__time">{{ formatTime(msg.createTime) }}</div>
            </div>

            <!-- 用户头像 -->
            <div v-if="msg.role === 'user'" class="message-avatar">
              <el-avatar :size="36" icon="UserFilled" />
            </div>
          </div>

          <!-- 发送中状态 -->
          <div v-if="sending" class="message-row message-row--self">
            <div class="message-bubble-wrapper">
              <div class="message-bubble message-bubble--user message-bubble--sending">
                <span>思考中…</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-main__input">
          <div class="input-row">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="输入消息…（Enter 发送，Shift+Enter 换行）"
              :disabled="sending"
              resize="none"
              @keydown="handleKeydown"
            />
            <el-button
              type="primary"
              :disabled="!inputMessage.trim() || sending"
              :loading="sending"
              @click="sendMessage"
              style="margin-left: 12px; align-self: flex-end"
            >
              发送
            </el-button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.report-assistant {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 900px;
  margin: 0 auto;

  &__body {
    display: flex;
    flex: 1;
    min-height: 0;
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 16px;
  }
}

/* ---------- 消息区 ---------- */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f5f6fa;

  &__empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  &__messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    min-height: 0;
  }

  &__input {
    padding: 12px 16px;
    background: #fff;
    border-top: 1px solid #ebeef5;
  }

  &__hints {
    margin-top: 20px;
    text-align: center;
  }

  &__hints-label {
    font-size: 13px;
    color: #909399;
    display: block;
    margin-bottom: 8px;
  }

  &__hint-tag {
    margin: 4px;
    cursor: pointer;
  }
}

/* ---------- 消息行 ---------- */
.message-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;

  &--self {
    flex-direction: row-reverse;
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-bubble-wrapper {
  max-width: 70%;
  margin: 0 10px;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;

  &--user {
    background: #409eff;
    color: #fff;
    border-bottom-right-radius: 2px;
  }

  &--assistant {
    background: #fff;
    color: #303133;
    border: 1px solid #ebeef5;
    border-bottom-left-radius: 2px;
  }

  &--sending {
    opacity: 0.7;
  }

  &__text {
    white-space: pre-wrap;
    word-break: break-word;
  }

  &__intent {
    margin-top: 8px;
  }

  &__hint {
    margin-top: 4px;
  }

  &__time {
    font-size: 11px;
    color: #c0c4cc;
    margin-top: 4px;

    .message-row--self & {
      text-align: right;
    }
  }
}

/* ---------- 输入区 ---------- */
.input-row {
  display: flex;
  align-items: flex-start;

  :deep(.el-textarea__inner) {
    resize: none;
  }
}
</style>
