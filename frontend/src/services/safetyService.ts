import apiClient from './apiClient'
import type {
  Device,
  GasReading,
  SafetyStatusResponse,
  ActiveLeakResponse,
  LeakHistoryResponse,
  DeviceDiagnosticsResponse,
  SimulatorStartRequest,
  SimulatorStatusResponse,
} from '@/types'

export const safetyService = {
  getDevices: async (): Promise<Device[]> => {
    const { data } = await apiClient.get('/devices/')
    return data
  },

  getSafetyStatus: async (deviceId: string): Promise<SafetyStatusResponse> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/safety`)
    return data
  },

  getGasReadings: async (deviceId: string, limit = 100): Promise<GasReading[]> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/gas-readings?limit=${limit}`)
    return data
  },

  getActiveLeak: async (deviceId: string): Promise<ActiveLeakResponse | null> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/leaks/active`)
    return data
  },

  getLeakHistory: async (deviceId: string, limit = 100): Promise<LeakHistoryResponse> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/leaks?limit=${limit}`)
    return data
  },

  getDiagnostics: async (deviceId: string): Promise<DeviceDiagnosticsResponse> => {
    const { data } = await apiClient.get(`/devices/${deviceId}/diagnostics`)
    return data
  },

  emergencyCloseValve: async (deviceId: string): Promise<Device> => {
    const { data } = await apiClient.post(`/devices/${deviceId}/valve/emergency-close`)
    return data
  },

  resetValve: async (deviceId: string): Promise<Device> => {
    const { data } = await apiClient.post(`/devices/${deviceId}/valve/reset`)
    return data
  },

  startSimulator: async (payload: SimulatorStartRequest): Promise<{ status: SimulatorStatusResponse }> => {
    const { data } = await apiClient.post('/simulator/start', payload)
    return data
  },

  stopSimulator: async (deviceId: string): Promise<{ status: SimulatorStatusResponse }> => {
    const { data } = await apiClient.post('/simulator/stop', { device_id: deviceId })
    return data
  },

  getSimulatorStatus: async (deviceId: string): Promise<SimulatorStatusResponse> => {
    const { data } = await apiClient.get(`/simulator/status/${deviceId}`)
    return data
  },
}

export default safetyService
