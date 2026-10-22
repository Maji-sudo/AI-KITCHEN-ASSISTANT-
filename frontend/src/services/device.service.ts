import apiClient from './apiClient'
import type { Device, Cylinder, GasReading, LeakEvent, WeightReading } from '@/types'

export const deviceService = {
  getDevices: async (): Promise<Device[]> => {
    const { data } = await apiClient.get('/devices/')
    return data
  },

  getDevice: async (id: string): Promise<Device> => {
    const { data } = await apiClient.get(`/devices/${id}`)
    return data
  },

  pairDevice: async (deviceId: string, name: string): Promise<Device> => {
    const { data } = await apiClient.post('/devices/', { id: deviceId, name })
    return data
  },

  removeDevice: async (id: string) => {
    return apiClient.delete(`/devices/${id}`)
  },

  getCylinders: async (deviceId: string): Promise<Cylinder[]> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/cylinders`)
    return data
  },

  getGasReadings: async (deviceId: string, limit = 100): Promise<GasReading[]> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/gas-readings?limit=${limit}`)
    return data
  },

  getWeightReadings: async (deviceId: string, limit = 100): Promise<WeightReading[]> => {
    const { data } = await apiClient.get(`/telemetry/weight/${deviceId}?limit=${limit}`)
    return data
  },

  getLeakEvents: async (deviceId: string): Promise<LeakEvent[]> => {
    const { data } = await apiClient.get(`/telemetry/leaks/${deviceId}`)
    return data
  },

  ingestGasReading: async (deviceId: string, ppmValue: number, status = 'normal') => {
    const { data } = await apiClient.post('/telemetry/gas', {
      device_id: deviceId,
      ppm_value: ppmValue,
      status,
      timestamp: new Date().toISOString(),
    })
    return data
  },

  ingestWeightReading: async (deviceId: string, weightG: number) => {
    const { data } = await apiClient.post('/telemetry/weight', {
      device_id: deviceId,
      weight_g: weightG,
      timestamp: new Date().toISOString(),
    })
    return data
  },
}
