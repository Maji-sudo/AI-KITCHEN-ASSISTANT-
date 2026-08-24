import apiClient from './apiClient'
import type { Booking } from '@/types'

export const bookingService = {
  // Get booking history
  getBookings: async (
    skip = 0,
    limit = 50
  ): Promise<Booking[]> => {
    try {
      const { data } = await apiClient.get(
        `/bookings/?skip=${skip}&limit=${limit}`
      )

      return data
    } catch (error: any) {
      console.error('Get bookings failed:', error)
      console.error('Response:', error?.response?.data)

      throw error
    }
  },

  // Create a new cylinder refill booking
  createBooking: async (payload: {
    device_id: string
    distributor: string
    booking_date: string
    source?: string
  }) => {
    try {
      const requestBody = {
        device_id: payload.device_id,
        distributor: payload.distributor,
        booking_date: payload.booking_date,
        source: payload.source ?? 'app',
        status: 'pending',
      }

      console.log('Creating booking:', requestBody)

      const { data } = await apiClient.post(
        '/bookings/',
        requestBody
      )

      console.log('Booking created:', data)

      return data
    } catch (error: any) {
      console.error('Create booking failed:', error)

      if (error?.response) {
        console.error('Status:', error.response.status)
        console.error('Backend response:', error.response.data)
      }

      throw error
    }
  },

  // Cancel booking
  cancelBooking: async (id: number) => {
    try {
      const { data } = await apiClient.patch(
        `/bookings/${id}/status?status=cancelled`
      )

      return data
    } catch (error: any) {
      console.error('Cancel booking failed:', error)
      console.error('Backend response:', error?.response?.data)

      throw error
    }
  },
}