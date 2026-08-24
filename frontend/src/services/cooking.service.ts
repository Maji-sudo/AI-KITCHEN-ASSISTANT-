import apiClient from './apiClient'
import type { Dish, CookingHistory } from '@/types'

export const cookingService = {
  getDishes: async (): Promise<Dish[]> => {
    const { data } = await apiClient.get('/cooking/dishes')
    return data
  },

  getHistory: async (skip = 0, limit = 50): Promise<CookingHistory[]> => {
    const { data } = await apiClient.get(`/cooking/history?skip=${skip}&limit=${limit}`)
    return data
  },

  logCooking: async (payload: {
    dish_id?: number
    device_id?: string
    actual_gas_g?: number
    actual_duration_min?: number
    logged_date?: string
  }) => {
    const { data } = await apiClient.post('/cooking/history', {
      ...payload,
      logged_date: payload.logged_date ?? new Date().toISOString(),
    })
    return data
  },

  estimateGas: (dishIds: number[], dishes: Dish[]) => {
    const total = dishIds.reduce((acc, id) => {
      const dish = dishes.find((d) => d.id === id)
      return acc + (dish?.base_gas_g ?? 0)
    }, 0)
    return { total_gas_g: total, dishes: dishIds.map((id) => dishes.find((d) => d.id === id)) }
  },

  // Calls the backend AI chat endpoint
  chat: async (message: string): Promise<string> => {
    try {
      const { data } = await apiClient.post('/cooking/chat', { message })
      return data.reply
    } catch (error) {
      console.error("Chat API failed:", error)
      return "I'm having trouble connecting to the backend. Please try again later."
    }
  },
}
