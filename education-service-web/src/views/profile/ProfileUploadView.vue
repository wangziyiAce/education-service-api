<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { profileApi } from '@/api/profile'
import PageHeader from '@/components/common/PageHeader.vue'

/* ---------- 来源类型 ---------- */
const sourceTypeOptions = [
  { label: 'PDF简历', value: 'pdf_resume' },
  { label: 'Excel表格', value: 'excel' },
  { label: '文本资料', value: 'text' },
  { label: '手动录入', value: 'manual' },
  { label: '导入数据', value: 'import' },
]

/* ---------- 左侧上传区 ---------- */
const uploadRef = ref()
const uploadFile = ref<File | null>(null)
const textContent = ref('')
const sourceType = ref('pdf_resume')
const uploading = ref(false)
const analyzing = ref(false)

/* ---------- 右侧结果区 ---------- */
type AnalyzeStatus = 'idle' | 'pending' | 'success' | 'failed'
const analyzeStatus = ref<AnalyzeStatus>('idle')
const sourceId = ref<number | null>(null)
const resultData = ref<any>(null)
const errorMessage = ref('')
const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null)

/* ---------- 文件变化 ---------- */
function handleFileChange(file: any) {
  uploadFile.value = file.raw || file
}

function handleFileRemove() {
  uploadFile.value = null
}

/* ---------- 开始研判 ---------- */
async function startAnalyze() {
  if (!uploadFile.value && !textContent.value.trim()) {
    ElMessage.warning('请上传文件或输入文本内容')
    return
  }

  uploading.value = true
  analyzeStatus.value = 'idle'
  resultData.value = null
  errorMessage.value = ''

  try {
    // 1. 上传资料
    const formData = new FormData()
    if (uploadFile.value) {
      formData.append('file', uploadFile.value)
    }
    formData.append('source_type', sourceType.value)
    if (textContent.value.trim()) {
      formData.append('content_text', textContent.value.trim())
    }

    const uploadRes: any = await profileApi.upload(formData)
    const sid = uploadRes?.id ?? uploadRes?.source_id
    if (!sid) {
      ElMessage.error('上传响应缺少 source_id')
      uploading.value = false
      return
    }
    sourceId.value = sid
    uploading.value = false

    // 2. 触发研判
    analyzing.value = true
    await profileApi.analyze(sid)
    analyzing.value = false

    // 3. 开始轮询
    analyzeStatus.value = 'pending'
    startPolling(sid)
  } catch (err: any) {
    uploading.value = false
    analyzing.value = false
    const msg = err?.message || err?.response?.data?.message || '研判启动失败'
    ElMessage.error(msg)
    analyzeStatus.value = 'failed'
    errorMessage.value = msg
  }
}

/* ---------- 轮询结果 ---------- */
function startPolling(sid: number) {
  let count = 0
  const maxCount = 120

  pollingTimer.value = setInterval(async () => {
    count++
    try {
      const res: any = await profileApi.getResult(sid)
      // 如果后端返回了明确状态字段
      const status = res?.parse_status
      if (status === 'success' || status === 'completed') {
        stopPolling()
        analyzeStatus.value = 'success'
        resultData.value = res
        ElMessage.success('研判完成')
      } else if (status === 'failed' || status === 'error') {
        stopPolling()
        analyzeStatus.value = 'failed'
        errorMessage.value = res?.error_message || res?.message || '研判失败'
        ElMessage.error(errorMessage.value)
      } else if (count >= maxCount) {
        stopPolling()
        analyzeStatus.value = 'failed'
        errorMessage.value = '研判超时，请稍后重试'
        ElMessage.error('研判超时')
      } else {
        // 仍在 pending / processing 中，继续轮询
      }
    } catch (err: any) {
      stopPolling()
      analyzeStatus.value = 'failed'
      errorMessage.value = err?.message || '获取结果失败'
      ElMessage.error(errorMessage.value)
    }
  }, 2000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

/* ---------- 重试 ---------- */
async function retryAnalyze() {
  if (!sourceId.value) {
    startAnalyze()
    return
  }
  analyzing.value = true
  try {
    await profileApi.analyze(sourceId.value)
    analyzing.value = false
    analyzeStatus.value = 'pending'
    errorMessage.value = ''
    startPolling(sourceId.value)
  } catch (err: any) {
    analyzing.value = false
    const msg = err?.message || '重试失败'
    ElMessage.error(msg)
  }
}

/* ---------- 进度条颜色 ---------- */
function matchProgressColor(score: number) {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="profile-upload">
    <PageHeader />
    <div class="profile-upload__body">
      <!-- 左侧：上传区 -->
      <div class="profile-upload__left">
        <div class="profile-upload__card">
          <h3 class="profile-upload__card-title">上传资料</h3>

          <el-upload
            ref="uploadRef"
            class="profile-upload__uploader"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf,.xls,.xlsx,.txt,.doc,.docx"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF / Excel / TXT / DOCX 格式，单文件上传
              </div>
            </template>
          </el-upload>

          <el-form label-width="80px" class="profile-upload__form">
            <el-form-item label="来源类型">
              <el-select v-model="sourceType" style="width: 100%">
                <el-option
                  v-for="opt in sourceTypeOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="文本内容">
              <el-input v-model="textContent" type="textarea" :rows="4" placeholder="或直接粘贴文本资料..." />
            </el-form-item>
          </el-form>

          <el-button
            type="primary"
            :loading="uploading || analyzing"
            :disabled="!uploadFile && !textContent.trim()"
            style="width: 100%"
            @click="startAnalyze"
          >
            {{ uploading ? '上传中...' : analyzing ? '启动研判...' : '开始研判' }}
          </el-button>
        </div>
      </div>

      <!-- 右侧：结果区 -->
      <div class="profile-upload__right">
        <div class="profile-upload__card profile-upload__result">
          <h3 class="profile-upload__card-title">研判结果</h3>

          <!-- 空闲状态 -->
          <el-empty
            v-if="analyzeStatus === 'idle'"
            description="请先上传文件并点击「开始研判」"
            :image-size="100"
          />

          <!-- 研判中 -->
          <div v-if="analyzeStatus === 'pending'" class="profile-upload__pending">
            <el-icon class="is-loading" :size="36"><UploadFilled /></el-icon>
            <p class="profile-upload__pending-text">研判中，请稍候...</p>
            <p class="profile-upload__pending-hint">系统正在分析客户资料，通常需要 1-2 分钟</p>
          </div>

          <!-- 成功 -->
          <div v-if="analyzeStatus === 'success' && resultData" class="profile-upload__success">
            <div class="profile-upload__match-item" v-if="resultData.matched_product">
              <span class="profile-upload__match-label">匹配产品</span>
              <span class="profile-upload__match-value">{{ resultData.matched_product }}</span>
            </div>

            <div class="profile-upload__match-item" v-if="resultData.match_score !== undefined">
              <span class="profile-upload__match-label">匹配度</span>
              <div class="profile-upload__progress-wrap">
                <el-progress
                  :percentage="Number(resultData.match_score)"
                  :color="matchProgressColor(Number(resultData.match_score))"
                  :stroke-width="16"
                />
              </div>
            </div>

            <div class="profile-upload__match-item" v-if="resultData.match_reason">
              <span class="profile-upload__match-label">匹配原因</span>
              <p class="profile-upload__match-reason">{{ resultData.match_reason }}</p>
            </div>

            <div class="profile-upload__plans" v-if="resultData.recommended_plans && resultData.recommended_plans.length">
              <span class="profile-upload__match-label">推荐方案</span>
              <ul class="profile-upload__plan-list">
                <li
                  v-for="(plan, idx) in resultData.recommended_plans"
                  :key="idx"
                  class="profile-upload__plan-item"
                >
                  <span class="profile-upload__plan-index">{{ idx + 1 }}.</span>
                  <span>{{ typeof plan === 'string' ? plan : (plan.name || plan.title || JSON.stringify(plan)) }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- 失败 -->
          <div v-if="analyzeStatus === 'failed'" class="profile-upload__failed">
            <el-result icon="error" title="研判失败" :sub-title="errorMessage || '未知错误'">
              <template #extra>
                <el-button type="primary" @click="retryAnalyze">重 试</el-button>
              </template>
            </el-result>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.profile-upload {
  max-width: 1200px;
  margin: 0 auto;
  &__body {
    display: flex;
    gap: 20px;
    padding: 16px;
  }
  &__left {
    flex: 0 0 400px;
  }
  &__right {
    flex: 1;
    min-width: 0;
  }
  &__card {
    background: #fff;
    border-radius: 4px;
    padding: 20px;
  }
  &__card-title {
    margin: 0 0 16px;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  &__uploader {
    width: 100%;
    margin-bottom: 16px;
  }
  &__form {
    margin-bottom: 12px;
  }
  &__result {
    min-height: 360px;
  }

  /* 研判中 */
  &__pending {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 0;
    color: #409eff;
  }
  &__pending-text {
    margin: 12px 0 4px;
    font-size: 16px;
    font-weight: 500;
  }
  &__pending-hint {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }

  /* 成功 */
  &__match-item {
    margin-bottom: 16px;
  }
  &__match-label {
    display: block;
    font-size: 13px;
    color: #909399;
    margin-bottom: 6px;
  }
  &__match-value {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }
  &__progress-wrap {
    max-width: 360px;
  }
  &__match-reason {
    margin: 0;
    font-size: 14px;
    color: #606266;
    line-height: 1.7;
    white-space: pre-wrap;
  }
  &__plans {
    margin-top: 16px;
  }
  &__plan-list {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
  }
  &__plan-item {
    padding: 6px 0;
    font-size: 14px;
    color: #303133;
    border-bottom: 1px solid #f0f0f0;
    &:last-child {
      border-bottom: none;
    }
  }
  &__plan-index {
    font-weight: 600;
    margin-right: 4px;
  }
}
</style>
