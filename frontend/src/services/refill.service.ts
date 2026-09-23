import apiClient from './apiClient'
import type { RefillPrediction } from '@/types'

export const refillService = {
  getLatestPrediction: async (deviceId: string): Promise<RefillPrediction> => {
    const { data } = await apiClient.get(`/refill/${deviceId}`)
    return data
  },

  getPredictionHistory: async (deviceId: string, limit = 10): Promise<RefillPrediction[]> => {
    const { data } = await apiClient.get(`/refill/${deviceId}/history?limit=${limit}`)
    return data
  },

  recomputePrediction: async (deviceId: string): Promise<RefillPrediction> => {
    const { data } = await apiClient.post(`/refill/${deviceId}/predict`)
    return data
  },
}
