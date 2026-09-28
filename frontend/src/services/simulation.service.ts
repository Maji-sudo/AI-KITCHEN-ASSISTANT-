import apiClient from './apiClient'
import type { Device, GasReading, WeightReading, CookingHistory } from '@/types'

export interface SimulationResult {
  success: boolean
  message: string
  details?: Record<string, any>
}

export const simulationService = {
  createSimulatedDevice: async (
    name = 'Kitchen SafeGas Hub',
    cylinderType = '14.2kg',
    deviceId?: string
  ): Promise<Device> => {
    const { data } = await apiClient.post('/simulation/device', {
      name,
      cylinder_type: cylinderType,
      device_id: deviceId,
    })
    return data
  },

  generateData: async (
    deviceId: string,
    days = 7,
    pattern = 'medium'
  ): Promise<SimulationResult> => {
    const { data } = await apiClient.post('/simulation/generate', {
      device_id: deviceId,
      days,
      pattern,
    })
    return data
  },

  triggerSafety: async (
    deviceId: string,
    scenario: 'normal' | 'warning' | 'critical'
  ): Promise<SimulationResult> => {
    const { data } = await apiClient.post('/simulation/safety', {
      device_id: deviceId,
      scenario,
    })
    return data
  },

  resetData: async (deviceId: string): Promise<SimulationResult> => {
    const { data } = await apiClient.post('/simulation/reset', {
      device_id: deviceId,
    })
    return data
  },

  manualGas: async (
    deviceId: string,
    ppmValue: number,
    status = 'normal'
  ): Promise<GasReading> => {
    const { data } = await apiClient.post('/telemetry/manual/gas', {
      device_id: deviceId,
      ppm_value: ppmValue,
      status,
      timestamp: new Date().toISOString(),
    })
    return data
  },

  manualWeight: async (
    deviceId: string,
    weightG: number
  ): Promise<WeightReading> => {
    const { data } = await apiClient.post('/telemetry/manual/weight', {
      device_id: deviceId,
      weight_g: weightG,
      timestamp: new Date().toISOString(),
    })
    return data
  },

  manualCooking: async (
    deviceId: string,
    cookingDurationMin: number,
    actualGasG: number,
    dishName?: string
  ): Promise<CookingHistory> => {
    const { data } = await apiClient.post('/simulation/manual/cooking', {
      device_id: deviceId,
      dish_name: dishName,
      cooking_duration_min: cookingDurationMin,
      actual_gas_g: actualGasG,
      logged_date: new Date().toISOString(),
    })
    return data
  },
}
