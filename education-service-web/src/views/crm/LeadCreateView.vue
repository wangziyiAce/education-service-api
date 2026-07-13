<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCrmStore } from '@/store/crm'
import { useAuthStore } from '@/store/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const crm = useCrmStore()
const auth = useAuthStore()

const formRef = ref()
const form = reactive({
  customer_name: '',
  contact_info: '',
  intended_country: '',
  intended_major: '',
  source_channel: '',
  remark: '',
  owner_employee_id: auth.user?.id || 1,  // 默认当前登录用户
})
const loading = ref(false)

const rules = {
  customer_name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await crm.createLead(form)
    ElMessage.success('新增客户成功')
    router.push('/crm/leads')
  } catch {
    ElMessage.error('新增失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="lead-create">
    <PageHeader />
    <div class="lead-create__body">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 700px">
        <el-form-item label="客户姓名" prop="customer_name">
          <el-input v-model="form.customer_name" placeholder="请输入" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact_info" placeholder="电话/邮箱" />
        </el-form-item>
        <el-form-item label="意向国家">
          <el-select v-model="form.intended_country" placeholder="请选择" clearable style="width: 100%">
            <el-option label="英国" value="英国" />
            <el-option label="德国" value="德国" />
            <el-option label="新加坡" value="新加坡" />
            <el-option label="澳大利亚" value="澳大利亚" />
            <el-option label="美国" value="美国" />
            <el-option label="加拿大" value="加拿大" />
          </el-select>
        </el-form-item>
        <el-form-item label="意向专业">
          <el-input v-model="form.intended_major" placeholder="请输入" />
        </el-form-item>
        <el-form-item label="来源渠道">
          <el-select v-model="form.source_channel" placeholder="请选择" clearable style="width: 100%">
            <el-option label="线上咨询" value="线上咨询" />
            <el-option label="转介绍" value="转介绍" />
            <el-option label="活动推广" value="活动推广" />
            <el-option label="电话外呼" value="电话外呼" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit" class="btn-submit">保存</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.lead-create {
  max-width: 800px;
  margin: 0 auto;
  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 24px;
  }
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

.btn-submit {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border: none;

  &:hover {
    background: linear-gradient(135deg, #66b1ff, #409eff);
  }
}
</style>
