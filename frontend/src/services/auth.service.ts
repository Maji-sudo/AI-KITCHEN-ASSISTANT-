import apiClient from './apiClient'
import type { User } from '@/types'

export interface RegisterPayload {
  name: string
  email: string
  phone?: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: number
  name: string
  email: string
  phone?: string | null
  is_new_user: boolean
  user?: User
}

export const authService = {
  /**
   * Register a new user with name, email, optional phone, and password.
   */
  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/auth/register', payload)

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_id', String(data.user_id))
    localStorage.setItem('user_name', data.name)
    localStorage.setItem('user_email', data.email || '')
    localStorage.setItem('user_phone', data.phone || '')

    return data
  },

  /**
   * Login user with email and password.
   */
  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/auth/login', payload)

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_id', String(data.user_id))
    localStorage.setItem('user_name', data.name)
    localStorage.setItem('user_email', data.email || '')
    localStorage.setItem('user_phone', data.phone || '')

    return data
  },

  /**
   * Update current user mobile number
   */
  updatePhone: async (phone: string): Promise<User> => {
    const { data } = await apiClient.patch<User>('/auth/me', { phone })
    localStorage.setItem('user_phone', data.phone || '')
    return data
  },

  /**
   * Fetch current user profile using stored JWT
   */
  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me')
    localStorage.setItem('user_id', String(data.id))
    localStorage.setItem('user_name', data.name)
    localStorage.setItem('user_email', data.email || '')
    localStorage.setItem('user_phone', data.phone ?? '')
    return data
  },

  /**
   * Clear tokens and cached user info
   */
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_name')
    localStorage.removeItem('user_email')
    localStorage.removeItem('user_phone')
  },
}
