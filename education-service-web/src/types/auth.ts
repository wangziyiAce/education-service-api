export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  real_name: string | null
  user_type: 'student' | 'employee' | 'admin' | 'visitor'
  role_id: number | null
  department: string | null
  contact_info: string | null
  avatar_url: string | null
  status: string
}

export interface UserCreate {
  username: string
  password: string
  real_name?: string
  user_type: string
  role_id?: number
  department?: string
  contact_info?: string
}

export interface UserUpdate {
  real_name?: string
  user_type?: string
  role_id?: number
  department?: string
  contact_info?: string
  status?: string
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

export interface RoleInfo {
  id: number
  role_code: string
  role_name: string
}

export interface OrganizationInfo {
  id: number
  org_name: string
  parent_id: number | null
  children?: OrganizationInfo[]
}
