export interface Lead {
  id: number
  customer_name: string
  contact_info: string | null
  intended_country: string | null
  intended_major: string | null
  source_channel: string | null
  status: 'new' | 'contacting' | 'qualified' | 'signed' | 'lost'
  owner_employee_id: number | null
  owner_name: string | null
  remark: string | null
  last_contact_time: string | null
  create_time: string
  update_time: string | null
}

export interface LeadCreate {
  customer_name: string
  contact_info?: string
  intended_country?: string
  intended_major?: string
  source_channel?: string
  remark?: string
}

export interface LeadUpdate {
  customer_name?: string
  contact_info?: string
  intended_country?: string
  intended_major?: string
  source_channel?: string
  remark?: string
}

export interface LeadStatusUpdate {
  status: string
}

export interface FollowUp {
  id: number
  lead_id: number
  employee_id: number | null
  employee_name: string | null
  content: string
  follow_up_time: string | null
  create_time: string
}

export interface FollowUpCreate {
  content: string
  follow_up_time?: string
}

export interface AssistantChatRequest {
  session_id?: string
  message: string
}

export interface AssistantChatResponse {
  session_id: string
  reply_text: string
  reply?: string
  action_type?: string | null
  action_data?: Record<string, any> | null
  intent?: string
}

export interface AssistantSession {
  id: number
  session_id: string
  title: string | null
  create_time: string
}

export interface AssistantMessage {
  id: number
  session_id: string
  role: 'user' | 'assistant'
  content: string
  create_time: string
}
