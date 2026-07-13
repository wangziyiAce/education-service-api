<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCrmStore } from '@/store/crm'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const crm = useCrmStore()

const leadId = Number(route.params.id)
const followUpContent = ref('')
const followUpLoading = ref(false)

async function handleStatusChange(newStatus: string) {
  try {
    await crm.changeStatus(leadId, { status: newStatus })
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('状态变更失败')
  }
}

async function handleAddFollowUp() {
  if (!followUpContent.value.trim()) {
    ElMessage.warning('请输入跟进内容')
    return
  }
  followUpLoading.value = true
  try {
    await crm.addFollowUp(leadId, { content: followUpContent.value })
    followUpContent.value = ''
    ElMessage.success('跟进记录已添加')
  } catch {
    ElMessage.error('添加失败')
  } finally {
    followUpLoading.value = false
  }
}

onMounted(() => {
  crm.fetchLeadDetail(leadId)
})
</script>

<template>
  <div class="lead-detail">
    <PageHeader>
      <template #actions>
        <el-button @click="router.push('/crm/leads')">返回列表</el-button>
      </template>
    </PageHeader>

    <div class="lead-detail__body" v-if="crm.currentLead" v-loading="crm.loading">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <StatusTag :status="crm.currentLead.status" category="lead" size="default" />
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户姓名">{{ crm.currentLead.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ crm.currentLead.contact_info || '-' }}</el-descriptions-item>
          <el-descriptions-item label="意向国家">{{ crm.currentLead.intended_country || '-' }}</el-descriptions-item>
          <el-descriptions-item label="意向专业">{{ crm.currentLead.intended_major || '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源渠道">{{ crm.currentLead.source_channel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ crm.currentLead.owner_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ crm.currentLead.create_time }}</el-descriptions-item>
          <el-descriptions-item label="最后联系">{{ crm.currentLead.last_contact_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ crm.currentLead.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 状态流转 -->
      <el-card class="info-card">
        <template #header><span>状态流转</span></template>
        <el-radio-group
          :model-value="crm.currentLead.status"
          @change="handleStatusChange"
        >
          <el-radio-button value="new">新线索</el-radio-button>
          <el-radio-button value="contacting">跟进中</el-radio-button>
          <el-radio-button value="qualified">已确认</el-radio-button>
          <el-radio-button value="signed">已签约</el-radio-button>
          <el-radio-button value="lost">已流失</el-radio-button>
        </el-radio-group>
      </el-card>

      <!-- 跟进记录 -->
      <el-card class="info-card">
        <template #header><span>跟进记录 ({{ crm.followUps.length }})</span></template>
        <el-timeline>
          <el-timeline-item
            v-for="item in crm.followUps"
            :key="item.id"
            :timestamp="item.create_time"
            placement="top"
          >
            <p>{{ item.content }}</p>
            <span v-if="item.employee_name" style="color: #909399; font-size: 12px">
              跟进人：{{ item.employee_name }}
            </span>
          </el-timeline-item>
        </el-timeline>
        <div class="follow-up-input">
          <el-input
            v-model="followUpContent"
            type="textarea"
            :rows="3"
            placeholder="输入跟进内容..."
          />
          <el-button
            type="primary"
            :loading="followUpLoading"
            style="margin-top: 12px"
            @click="handleAddFollowUp"
          >
            添加跟进
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.lead-detail {
  max-width: 900px;
  margin: 0 auto;
  &__body {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
}

.info-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  :deep(.el-descriptions) {
    .el-descriptions__body .el-descriptions__table {
      border-color: #e8ecf1;
    }
  }
}

.follow-up-input {
  margin-top: 16px;
}

:deep(.el-timeline-item__node) {
  background-color: #e8ecf1;
}
</style>
