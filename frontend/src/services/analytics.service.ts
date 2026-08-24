import apiClient from './apiClient'
import type { UsageAnalytics, PeriodType } from '@/types'

export const analyticsService = {
  getAnalytics: async (deviceId: string, period: PeriodType, limit = 30): Promise<UsageAnalytics[]> => {
    const { data } = await apiClient.get(`/analytics/${deviceId}?period_type=${period}&limit=${limit}`)
    return data
  },

  getSummary: async (deviceId: string, period: PeriodType) => {
    const { data } = await apiClient.get(`/analytics/${deviceId}/summary?period_type=${period}`)
    return data
  },
}
