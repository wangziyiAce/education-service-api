export interface LeaveRecord {
  id: number
  student_id: number
  student_name: string | null
  leave_type: string
  reason: string | null
  start_date: string
  end_date: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  approver_id: number | null
  create_time: string
}

export interface LeaveCreate {
  student_id: number
  leave_type: string
  reason?: string
  start_date: string
  end_date: string
}

export interface LeaveApprove {
  approver_id: number
  status: 'approved' | 'rejected'
  comment?: string
}

export interface FeedbackTicket {
  id: number
  student_id: number
  student_name: string | null
  ticket_type: string
  content: string
  status: 'pending' | 'processing' | 'resolved'
  handler_id: number | null
  create_time: string
}

export interface FeedbackCreate {
  student_id: number
  ticket_type: string
  content: string
}

export interface FeedbackUpdate {
  status: string
  handler_id?: number
  handler_comment?: string
}

export interface PsychAlert {
  id: number
  student_id: number
  student_name: string | null
  risk_level: 'low' | 'medium' | 'high'
  trigger_reason: string | null
  status: string
  create_time: string
}

export interface PsychAlertUpdate {
  status: string
  handler_id?: number
  handler_comment?: string
}

export interface Score {
  id: number
  student_id: number
  course_name: string
  score: number
  semester: string
  credit: number | null
}

export interface ApplicationProgress {
  id: number
  student_id: number
  university_name: string
  program_name: string | null
  status: string
  submit_date: string | null
  remark: string | null
}

export interface AcademicDeadline {
  id: number
  student_id: number
  title: string
  deadline: string
  description: string | null
  is_completed: number
}

export interface StudentNotification {
  id: number
  student_id: number
  title: string
  content: string
  is_read: number
  create_time: string
}
