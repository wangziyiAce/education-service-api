import { defineStore } from 'pinia'
import { ref } from 'vue'
import { crmApi } from '@/api/crm'
import type { Lead, LeadCreate, LeadUpdate, LeadStatusUpdate, FollowUp, FollowUpCreate } from '@/types/crm'
import type { PaginatedData } from '@/types/api'

export const useCrmStore = defineStore('crm', () => {
  const leads = ref<Lead[]>([])
  const total = ref(0)
  const currentLead = ref<Lead | null>(null)
  const followUps = ref<FollowUp[]>([])
  const loading = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(20)

  async function fetchLeads(params?: Record<string, any>) {
    loading.value = true
    try {
      const res: PaginatedData<Lead> = await crmApi.listLeads({
        page: currentPage.value,
        page_size: pageSize.value,
        ...params,
      })
      leads.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchLeadDetail(id: number) {
    loading.value = true
    try {
      currentLead.value = await crmApi.getLead(id)
      followUps.value = await crmApi.listFollowUps(id)
    } finally {
      loading.value = false
    }
  }

  async function createLead(data: LeadCreate) {
    const lead = await crmApi.createLead(data)
    await fetchLeads()
    return lead
  }

  async function updateLead(id: number, data: LeadUpdate) {
    const lead = await crmApi.updateLead(id, data)
    if (currentLead.value?.id === id) {
      currentLead.value = lead
    }
    return lead
  }

  async function changeStatus(id: number, data: LeadStatusUpdate) {
    const lead = await crmApi.changeStatus(id, data)
    if (currentLead.value?.id === id) {
      currentLead.value = lead
    }
    await fetchLeads()
    return lead
  }

  async function addFollowUp(leadId: number, data: FollowUpCreate) {
    const followUp = await crmApi.addFollowUp(leadId, data)
    followUps.value.push(followUp)
    return followUp
  }

  return {
    leads,
    total,
    currentLead,
    followUps,
    loading,
    currentPage,
    pageSize,
    fetchLeads,
    fetchLeadDetail,
    createLead,
    updateLead,
    changeStatus,
    addFollowUp,
  }
})
