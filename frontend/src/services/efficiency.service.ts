import apiClient from './apiClient'
import type { EfficiencyScore } from '@/types'

export const efficiencyService = {
  getLatest: async (deviceId: string, limit = 5): Promise<EfficiencyScore[]> => {
    const { data } = await apiClient.get(`/efficiency/${deviceId}?limit=${limit}`)
    return data
  },

  // Convenience: return the single most recent score
  getScore: async (deviceId: string): Promise<EfficiencyScore | null> => {
    const { data } = await apiClient.get(`/efficiency/${deviceId}?limit=1`)
    return data?.[0] ?? null
  },
}
