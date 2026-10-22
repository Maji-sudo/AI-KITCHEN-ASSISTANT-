import apiClient from './apiClient'
import type { GasAgenciesResponse } from '@/types'

export const gasAgencyService = {
  /**
   * Search for nearby LPG gas agencies and distributors by GPS coordinates.
   */
  getNearbyAgencies: async (
    latitude: number,
    longitude: number,
    radius = 10000,
    query?: string
  ): Promise<GasAgenciesResponse> => {
    const params = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
      radius: String(radius),
    })

    if (query && query.trim()) {
      params.append('query', query.trim())
    }

    const { data } = await apiClient.get<GasAgenciesResponse>(
      `/gas-agencies/nearby?${params.toString()}`
    )
    return data
  },

  /**
   * Search for LPG gas agencies by area name or query string.
   */
  searchAgencies: async (
    query: string,
    latitude?: number,
    longitude?: number,
    radius = 10000
  ): Promise<GasAgenciesResponse> => {
    const params = new URLSearchParams({
      query: query.trim(),
      radius: String(radius),
    })

    if (latitude !== undefined && longitude !== undefined) {
      params.append('latitude', String(latitude))
      params.append('longitude', String(longitude))
    }

    const { data } = await apiClient.get<GasAgenciesResponse>(
      `/gas-agencies/search?${params.toString()}`
    )
    return data
  },
}
