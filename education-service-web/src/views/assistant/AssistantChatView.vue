<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/api/request'
import type { AssistantSession, AssistantMessage, AssistantChatRequest, AssistantChatResponse } from '@/types/crm'

/* ---------- 会话列表 ---------- */
const sessions = ref<AssistantSession[]>([])
const sessionsLoading = ref(false)

/* ---------- 当前会话 ---------- */
const currentSessionId = ref<string | null>(null)
const messages = ref<AssistantMessage[]>([])
const messagesLoading = ref(false)
const sending = ref(false)

/* ---------- 输入 ---------- */
const inputMessage = ref('')
const hints = [
  '查询所有意向客户',
  '今天新增了几个客户',
  '新增客户：王小明 13800009999',
  '查看今天的日报汇总',
]

/* ---------- 消息区 DOM 引用 ---------- */
const messagesContainer = ref<HTMLDivElement | null>(null)

/* ---------- 获取会话列表 ---------- */
async function fetchSessions() {
  sessionsLoading.value = true
  try {
    const data: any = await request.get('/assistant/sessions')
    if (Array.isArray(data)) {
      sessions.value = data
    } else if (data?.items) {
      sessions.value = data.items
    } else if (data?.sessions) {
      sessions.value = data.sessions
    } else {
      sessions.value = []
    }
  } catch {
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

/* ---------- 获取会话消息 ---------- */
async function fetchMessages(sessionId: string) {
  messagesLoading.value = true
  try {
    const data: any = await request.get(`/assistant/sessions/${sessionId}/messages`)
    if (Array.isArray(data)) {
      messages.value = data
    } else if (data?.items) {
      messages.value = data.items
    } else if (data?.messages) {
      messages.value = data.messages
    } else {
      messages.value = []
    }
  } catch {
    messages.value = []
  } finally {
    messagesLoading.value = false
  }
}

/* ---------- 选择会话 ---------- */
async function selectSession(sessionId: string) {
  currentSessionId.value = sessionId
  await fetchMessages(sessionId)
  scrollToBottom()
}

/* ---------- 新建会话 ---------- */
function newConversation() {
  currentSessionId.value = null
  messages.value = []
  inputMessage.value = ''
}

/* ---------- 发送消息 ---------- */
async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || sending.value) return

  inputMessage.value = ''
  sending.value = true

  // 构建请求体
  const body: AssistantChatRequest = {
    message: text,
    session_id: currentSessionId.value ?? undefined,
  }

  // 乐观添加用户消息到列表
  const tempUserMsg: AssistantMessage = {
    id: Date.now(),
    session_id: currentSessionId.value ?? '',
    role: 'user',
    content: text,
    create_time: new Date().toISOString(),
  }
  messages.value.push(tempUserMsg)
  scrollToBottom()

  try {
    const res: AssistantChatResponse = await request.post('/assistant/chat', body)

    // 首次发送：保存后端返回的 session_id
    if (!currentSessionId.value && res.session_id) {
      currentSessionId.value = res.session_id
      // 更新临时消息的 session_id
      tempUserMsg.session_id = res.session_id
      // 刷新会话列表
      fetchSessions()
    }

    // 添加助手回复
    const assistantMsg: any = {
      id: Date.now() + 1,
      session_id: res.session_id || currentSessionId.value || '',
      role: 'assistant',
      content: res.reply_text,
      action_type: res.action_type,
      action_data: res.action_data,
      create_time: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)
    scrollToBottom()
  } catch {
    // 发送失败，移除临时用户消息
    messages.value = messages.value.filter((m: AssistantMessage) => m.id !== tempUserMsg.id)
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

function formatSessionTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  // 同一天只显示时间
  if (d.toDateString() === now.toDateString()) {
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  return `${d.getMonth() + 1}/${d.getDate()}`
}

/* ---------- 会话标题 ---------- */
function sessionTitle(session: AssistantSession, index: number): string {
  // AssistantSession 类型有 title 字段
  if ((session as any).title) return (session as any).title
  return `会话 ${index + 1}`
}

/* ---------- 初始化 ---------- */
onMounted(() => {
  fetchSessions()
})

/* ---------- 切换会话时滚动 ---------- */
watch(currentSessionId, () => {
  scrollToBottom()
})
</script>

<template>
  <div class="assistant-chat">
    <PageHeader>
      <template #actions>
        <span style="color: #909399; font-size: 13px">企业智能助手</span>
      </template>
    </PageHeader>

    <div class="assistant-chat__body">
      <!-- 左侧会话列表 -->
      <aside class="chat-sidebar">
        <div class="chat-sidebar__header">
          <el-button type="primary" size="small" style="width: 100%" @click="newConversation">
            + 新建会话
          </el-button>
        </div>

        <div class="chat-sidebar__list" v-loading="sessionsLoading">
          <div
            v-for="(session, index) in sessions"
            :key="session.session_id"
            class="session-item"
            :class="{ 'session-item--active': currentSessionId === session.session_id }"
            @click="selectSession(session.session_id)"
          >
            <div class="session-item__avatar">
              <el-avatar :size="36" icon="UserFilled" />
            </div>
            <div class="session-item__info">
              <div class="session-item__name">{{ sessionTitle(session, index) }}</div>
              <div class="session-item__time">{{ formatSessionTime(session.create_time) }}</div>
            </div>
          </div>

          <el-empty
            v-if="!sessionsLoading && sessions.length === 0"
            description="暂无会话"
            :image-size="60"
          />
        </div>
      </aside>

      <!-- 右侧消息区 -->
      <main class="chat-main">
        <!-- 未选择会话且无消息 -->
        <div v-if="!currentSessionId && messages.length === 0" class="chat-main__empty">
          <el-icon :size="64" color="#dcdfe6"><ChatDotRound /></el-icon>
          <p style="color: #909399; margin-top: 16px">新建会话或在左侧选择历史会话</p>
          <div class="chat-main__hints">
            <span class="chat-main__hints-label">试试这些：</span>
            <el-tag v-for="h in hints" :key="h" class="chat-main__hint-tag" @click="inputMessage = h; sendMessage()">{{ h }}</el-tag>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-if="currentSessionId || messages.length > 0" ref="messagesContainer" class="chat-main__messages" v-loading="messagesLoading">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-row"
            :class="{ 'message-row--self': msg.role === 'user' }"
          >
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
                <!-- 展示 SQL/API 执行结果 -->
                <div v-if="(msg as any).action_data" class="message-bubble__data">
                  <el-table :data="(msg as any).action_data?.rows || []" size="small" border style="margin-top:8px" max-height="200">
                    <el-table-column v-for="(_, key) in ((msg as any).action_data?.rows || [])[0] || {}" :key="key" :prop="key" :label="key" min-width="80" />
                  </el-table>
                </div>
              </div>
              <div class="message-bubble__time">{{ formatTime(msg.create_time) }}</div>
            </div>

            <div v-if="msg.role === 'user'" class="message-avatar">
              <el-avatar :size="36" icon="UserFilled" />
            </div>
          </div>

          <div v-if="sending" class="message-row message-row--self">
            <div class="message-bubble-wrapper">
              <div class="message-bubble message-bubble--user message-bubble--sending">
                <span>思考中…</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区（始终可见） -->
        <div class="chat-main__input">
          <div class="input-row">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="输入消息…（Enter发送，Shift+Enter换行）"
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
.assistant-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 1200px;
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

/* ---------- 左侧会话列表 ---------- */
.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  background: #fafafa;

  &__header {
    padding: 12px;
    border-bottom: 1px solid #ebeef5;
  }

  &__list {
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;

  &:hover {
    background: #ecf5ff;
  }

  &--active {
    background: #ecf5ff;
  }

  &__avatar {
    margin-right: 10px;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__name {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__time {
    font-size: 12px;
    color: #c0c4cc;
    margin-top: 2px;
  }
}

/* ---------- 右侧消息区 ---------- */
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
  max-width: 65%;
  margin: 0 10px;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;

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

  &__time {
    font-size: 11px;
    color: #c0c4cc;
    margin-top: 4px;

    .message-row--self & {
      text-align: right;
    }
  }
}

.chat-main {
  &__hints { margin-top: 20px; text-align: center; }
  &__hints-label { font-size: 13px; color: #909399; display: block; margin-bottom: 8px; }
  &__hint-tag { margin: 4px; cursor: pointer; }
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
