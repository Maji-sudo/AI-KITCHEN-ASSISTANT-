import apiClient from './apiClient'
import type { Recommendation } from '@/types'

export const recommendationService = {
  getRecommendations: async (skip = 0, limit = 50): Promise<Recommendation[]> => {
    const { data } = await apiClient.get(`/recommendations/?skip=${skip}&limit=${limit}`)
    return data
  },

  dismiss: async (id: number) => {
    const { data } = await apiClient.patch(`/recommendations/${id}/dismiss`)
    return data
  },

  act: async (id: number) => {
    const { data } = await apiClient.patch(`/recommendations/${id}/act`)
    return data
  },
}
