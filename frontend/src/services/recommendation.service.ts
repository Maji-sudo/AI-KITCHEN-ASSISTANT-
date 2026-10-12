import apiClient from './apiClient'
import type { Recommendation, RecommendationCounts, GenerateResponse } from '@/types'

export const recommendationService = {
  /** Return active (or all) recommendations for the logged-in user. */
  getRecommendations: async (
    skip = 0,
    limit = 50,
    includeAll = false,
  ): Promise<Recommendation[]> => {
    const { data } = await apiClient.get<Recommendation[]>('/recommendations/', {
      params: { skip, limit, include_all: includeAll },
    })
    return data
  },

  /** Return {active, acted, dismissed} counts — used for the dashboard summary bar. */
  getCounts: async (): Promise<RecommendationCounts> => {
    const { data } = await apiClient.get<RecommendationCounts>('/recommendations/counts')
    return data
  },

  /**
   * Trigger the rule-based engine for a given device.
   * Clears old active recommendations then returns the freshly generated set.
   */
  generate: async (deviceId: string, days = 30): Promise<GenerateResponse> => {
    const { data } = await apiClient.post<GenerateResponse>('/recommendations/generate', {
      device_id: deviceId,
      days,
    })
    return data
  },

  /** Mark a recommendation as dismissed. */
  dismiss: async (id: number): Promise<Recommendation> => {
    const { data } = await apiClient.patch<Recommendation>(`/recommendations/${id}/dismiss`)
    return data
  },

  /** Mark a recommendation as acted upon (completed). */
  act: async (id: number): Promise<Recommendation> => {
    const { data } = await apiClient.patch<Recommendation>(`/recommendations/${id}/act`)
    return data
  },
}
