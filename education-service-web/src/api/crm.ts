import request from './request'
import type { Lead, LeadCreate, LeadUpdate, LeadStatusUpdate, FollowUp, FollowUpCreate } from '@/types/crm'
import type { PaginatedData } from '@/types/api'

export const crmApi = {
  listLeads: (params?: Record<string, any>): Promise<PaginatedData<Lead>> =>
    request.get('/crm/leads', { params }),

  getLead: (id: number): Promise<Lead> =>
    request.get(`/crm/leads/${id}`),

  createLead: (data: LeadCreate): Promise<Lead> =>
    request.post('/crm/leads', data),

  updateLead: (id: number, data: LeadUpdate): Promise<Lead> =>
    request.put(`/crm/leads/${id}`, data),

  changeStatus: (id: number, data: LeadStatusUpdate): Promise<Lead> =>
    request.put(`/crm/leads/${id}/status`, data),

  listFollowUps: (leadId: number): Promise<FollowUp[]> =>
    request.get(`/crm/leads/${leadId}/follow-ups`),

  addFollowUp: (leadId: number, data: FollowUpCreate): Promise<FollowUp> =>
    request.post(`/crm/leads/${leadId}/follow-ups`, data),
}
