import apiClient from './apiClient'
import type { Notification } from '@/types'

export const notificationService = {
  getAll: async (skip = 0, limit = 50): Promise<Notification[]> => {
    const { data } = await apiClient.get(`/notifications/?skip=${skip}&limit=${limit}`)
    return data
  },

  // read/preference updates are UI-only for now (no backend endpoint yet)
  markRead: async (id: number) => { void id },
  markAllRead: async () => {},
  updatePreferences: async (prefs: Record<string, boolean>) => { void prefs },
}
