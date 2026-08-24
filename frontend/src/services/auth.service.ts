import apiClient from './apiClient'
import type { AuthTokens, OTPRequestPayload, OTPVerifyPayload, User } from '@/types'

export const authService = {
  requestOTP: async (payload: OTPRequestPayload) => {
    const { data } = await apiClient.post('/auth/request-otp', payload)
    return data
  },

  verifyOTP: async (payload: OTPVerifyPayload): Promise<AuthTokens & { name: string; user_id: number }> => {
    const { data } = await apiClient.post('/auth/verify-otp', payload)
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token)
      // Store user info for quick access
      localStorage.setItem('user_name', data.name ?? '')
      localStorage.setItem('user_id', String(data.user_id ?? ''))
    }
    return data
  },

  getMe: async (): Promise<User> => {
    // Return from localStorage until a /me endpoint is added
    return {
      id: parseInt(localStorage.getItem('user_id') ?? '0'),
      name: localStorage.getItem('user_name') ?? 'User',
      phone: '',
      language_pref: 'en',
      created_at: new Date().toISOString(),
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_name')
    localStorage.removeItem('user_id')
  },
}
