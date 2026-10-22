import apiClient from './apiClient'
import type {
  SettingsData,
  DeliveryAddress,
  NotificationPreferences,
  SafetyPreferences,
} from '@/types'

export const settingsService = {
  getSettings: async (): Promise<SettingsData> => {
    const { data } = await apiClient.get<SettingsData>('/settings/')
    return data
  },

  updateProfile: async (profile: {
    name?: string
    phone?: string
    language_pref?: string
  }): Promise<{ message: string; profile: SettingsData['profile'] }> => {
    const { data } = await apiClient.put('/settings/profile', profile)
    return data
  },

  saveAddress: async (address: {
    address_line: string
    area: string
    city: string
    state: string
    pincode: string
  }): Promise<{ message: string; delivery_address: DeliveryAddress }> => {
    const { data } = await apiClient.put('/settings/address', address)
    return data
  },

  clearAddress: async (): Promise<{ message: string; delivery_address: null }> => {
    const { data } = await apiClient.delete('/settings/address')
    return data
  },

  updateNotificationPreferences: async (
    preferences: NotificationPreferences
  ): Promise<{ message: string; notification_preferences: NotificationPreferences }> => {
    const { data } = await apiClient.put('/settings/notifications', preferences)
    return data
  },

  updateSafetyPreferences: async (
    preferences: SafetyPreferences
  ): Promise<{ message: string; safety_preferences: SafetyPreferences }> => {
    const { data } = await apiClient.put('/settings/safety', preferences)
    return data
  },
}
