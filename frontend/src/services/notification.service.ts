import apiClient from './apiClient'
import type { Notification } from '@/types'

export const notificationService = {
  getAll: async (
    skip = 0,
    limit = 50,
    filter?: string,
    unreadOnly = false
  ): Promise<Notification[]> => {
    let url = `/notifications/?skip=${skip}&limit=${limit}`
    if (filter && filter !== 'all') {
      url += `&filter=${encodeURIComponent(filter)}`
    }
    if (unreadOnly) {
      url += `&unread_only=true`
    }
    const { data } = await apiClient.get<Notification[]>(url)
    return data
  },

  getUnreadCount: async (): Promise<number> => {
    const { data } = await apiClient.get<{ unread_count: number }>('/notifications/unread-count')
    return data.unread_count
  },

  markRead: async (id: number): Promise<Notification> => {
    const { data } = await apiClient.patch<Notification>(`/notifications/${id}/read`)
    return data
  },

  markAllRead: async (): Promise<{ message: string; count: number }> => {
    const { data } = await apiClient.post<{ message: string; count: number }>('/notifications/read-all')
    return data
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.delete<{ message: string }>(`/notifications/${id}`)
    return data
  },

  clear: async (all = false): Promise<{ message: string; count: number }> => {
    const { data } = await apiClient.delete<{ message: string; count: number }>(`/notifications/?all=${all}`)
    return data
  },
}
