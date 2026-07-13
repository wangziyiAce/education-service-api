import { defineStore } from 'pinia'
import { ref } from 'vue'
import { studentApi } from '@/api/student'
import type { LeaveRecord, LeaveCreate, LeaveApprove, FeedbackTicket, FeedbackCreate, FeedbackUpdate, PsychAlert, PsychAlertUpdate } from '@/types/student'
import type { PaginatedData } from '@/types/api'

export const useStudentStore = defineStore('student', () => {
  const leaves = ref<LeaveRecord[]>([])
  const leavesTotal = ref(0)
  const feedbacks = ref<FeedbackTicket[]>([])
  const feedbacksTotal = ref(0)
  const psychAlerts = ref<PsychAlert[]>([])
  const psychTotal = ref(0)
  const loading = ref(false)

  // 请假
  async function fetchLeaves(params: { student_id: number; status?: string; page?: number; page_size?: number }) {
    loading.value = true
    try {
      const res: PaginatedData<LeaveRecord> = await studentApi.listLeaves(params)
      leaves.value = res.items
      leavesTotal.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createLeave(data: LeaveCreate) {
    return await studentApi.createLeave(data)
  }

  async function approveLeave(requestId: number, data: LeaveApprove) {
    return await studentApi.approveLeave(requestId, data)
  }

  // 投诉
  async function fetchFeedbacks(params: { student_id: number; status?: string; page?: number; page_size?: number }) {
    loading.value = true
    try {
      const res: PaginatedData<FeedbackTicket> = await studentApi.listFeedbacks(params)
      feedbacks.value = res.items
      feedbacksTotal.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function createFeedback(data: FeedbackCreate) {
    return await studentApi.createFeedback(data)
  }

  async function updateFeedback(ticketId: number, data: FeedbackUpdate) {
    return await studentApi.updateFeedback(ticketId, data)
  }

  // 心理预警
  async function fetchPsychAlerts(params?: { risk_level?: string; status?: string }) {
    loading.value = true
    try {
      const res: PaginatedData<PsychAlert> = await studentApi.listPsychAlerts(params)
      psychAlerts.value = res.items
      psychTotal.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function handlePsychAlert(alertId: number, data: PsychAlertUpdate) {
    return await studentApi.handlePsychAlert(alertId, data)
  }

  return {
    leaves, leavesTotal, feedbacks, feedbacksTotal, psychAlerts, psychTotal, loading,
    fetchLeaves, createLeave, approveLeave,
    fetchFeedbacks, createFeedback, updateFeedback,
    fetchPsychAlerts, handlePsychAlert,
  }
})
