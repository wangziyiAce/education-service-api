<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCrmStore } from '@/store/crm'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'

const router = useRouter()
const crm = useCrmStore()

const columns = [
  { prop: 'customer_name', label: '客户姓名', minWidth: 100 },
  { prop: 'contact_info', label: '联系方式', minWidth: 130 },
  { prop: 'intended_country', label: '意向国家', minWidth: 100 },
  { prop: 'intended_major', label: '意向专业', minWidth: 100 },
  { prop: 'source_channel', label: '来源渠道', minWidth: 90 },
  { prop: 'owner_name', label: '负责人', minWidth: 80 },
  { prop: 'last_contact_time', label: '最后联系', minWidth: 110 },
]

function getStatusCategory(status: string): 'lead' {
  return 'lead'
}

function handleCreate() {
  router.push('/crm/leads/create')
}

function handleRowClick(row: any) {
  router.push(`/crm/leads/${row.id}`)
}

function handlePageChange(page: number) {
  crm.currentPage = page
  crm.fetchLeads()
}

onMounted(() => {
  crm.fetchLeads()
})
</script>

<template>
  <div class="lead-list">
    <PageHeader>
      <template #actions>
        <el-button type="primary" @click="handleCreate">+ 新增客户</el-button>
      </template>
    </PageHeader>
    <div class="lead-list__body">
      <el-table
        :data="crm.leads"
        v-loading="crm.loading"
        stripe
        @row-click="handleRowClick"
        style="cursor: pointer"
        class="lead-table"
      >
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.minWidth"
        />
        <el-table-column label="状态" min-width="80">
          <template #default="{ row }">
            <StatusTag :status="row.status" :category="getStatusCategory(row.status)" />
          </template>
        </el-table-column>
      </el-table>
      <div class="lead-list__pagination">
        <el-pagination
          v-model:current-page="crm.currentPage"
          :page-size="crm.pageSize"
          :total="crm.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.lead-list {
  max-width: 1200px;
  margin: 0 auto;
  &__body {
    background: #fff;
    border-radius: 4px;
    padding: 16px;
    margin-top: 8px;
  }
  &__pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

.lead-table {
  :deep(.el-table__header-wrapper) {
    .el-table__header th {
      background-color: #f0f5ff;
    }
  }

  :deep(.el-table__body-wrapper) {
    .el-table__row {
      transition: transform 0.2s ease, box-shadow 0.2s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        position: relative;
        z-index: 1;
      }
    }
  }
}
</style>
