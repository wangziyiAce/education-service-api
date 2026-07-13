export interface Course {
  id: number
  project_name: string
  category: string | null
  description: string | null
  target_audience: string | null
  price: string | null
  duration: string | null
  tags: string[] | null
  status: number
  create_time: string
}

export interface Event {
  id: number
  event_name: string
  event_type: 'online' | 'offline' | 'hybrid'
  description: string | null
  start_time: string
  end_time: string | null
  location: string | null
  max_participants: number | null
  current_participants: number
  organizer_id: number | null
  status: 'upcoming' | 'ongoing' | 'ended' | 'cancelled'
  create_time: string
}

export interface EventRegistrationCreate {
  user_id?: number | null
  customer_name?: string
  contact_info?: string
  remark?: string
}

export interface EventRegistration {
  id: number
  event_id: number
  event_name: string | null
  user_id: number | null
  customer_name: string | null
  contact_info: string | null
  status: string
  create_time: string
}

export interface ChatSession {
  id: number
  session_id: string
  user_id: number | null
  visitor_name: string | null
  visitor_contact: string | null
  status: string
  last_message_time: string | null
  create_time: string
}

export interface ChatMessage {
  id: number
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  intent: string | null
  tokens_used: number | null
  response_time_ms: number | null
  create_time: string
}
