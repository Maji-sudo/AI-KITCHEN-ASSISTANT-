import apiClient from './apiClient'

export interface DailyConsumptionItem {
  date: string
  consumption_g: number
  consumption_kg: number
  reading_count: number
}

export interface DailyConsumptionResponse {
  device_id: string
  days: number
  total_consumption_g: number
  total_consumption_kg: number
  avg_daily_g: number
  avg_daily_kg: number
  records: DailyConsumptionItem[]
}

export interface WeeklyConsumptionItem {
  week_label: string
  start_date: string
  end_date: string
  total_consumption_g: number
  total_consumption_kg: number
  daily_avg_g: number
  daily_records: DailyConsumptionItem[]
}

export interface WeeklyConsumptionResponse {
  device_id: string
  weeks: number
  total_consumption_g: number
  total_consumption_kg: number
  records: WeeklyConsumptionItem[]
}

export interface MonthlyConsumptionItem {
  month_label: string
  year: number
  month: number
  total_consumption_g: number
  total_consumption_kg: number
  daily_avg_g: number
}

export interface MonthlyConsumptionResponse {
  device_id: string
  months: number
  total_consumption_g: number
  total_consumption_kg: number
  records: MonthlyConsumptionItem[]
}

export interface AverageConsumptionResponse {
  device_id: string
  avg_daily_g: number
  avg_daily_kg: number
  avg_weekly_g: number
  avg_weekly_kg: number
  total_days_analyzed: number
}

export interface UsagePatternSlot {
  slot_name: 'Morning' | 'Afternoon' | 'Evening' | 'Night'
  time_range: string
  consumption_g: number
  consumption_kg: number
  percentage: number
  drop_events_count: number
}

export interface UsagePatternResponse {
  device_id: string
  peak_period: string
  slots: UsagePatternSlot[]
  total_consumption_g: number
}

export interface PeakUsageResponse {
  device_id: string
  highest_day_date?: string | null
  highest_day_consumption_g: number
  highest_day_consumption_kg: number
  peak_period: string
  max_single_drop_g: number
}

export interface ConsumptionTrendResponse {
  device_id: string
  trend: 'increasing' | 'decreasing' | 'stable'
  percent_change: number
  recent_period_avg_g: number
  prior_period_avg_g: number
  description: string
}

export interface LeakEventItem {
  id: number
  start_time: string
  end_time?: string | null
  peak_ppm: number
  auto_shutoff_triggered: boolean
  false_alarm: boolean
}

export interface LeakSummaryResponse {
  device_id: string
  total_leaks: number
  auto_shutoffs_triggered: number
  peak_ppm: number
  recent_events: LeakEventItem[]
}

export interface EfficiencyScoreResponse {
  device_id: string
  overall_score: number
  grade: 'A' | 'B' | 'C' | 'D'
  explanation: string
  components_json: {
    safety_score?: number
    consumption_consistency?: number
    idle_usage_efficiency?: number
    leak_events_count?: number
    peak_ppm?: number
    night_usage_percentage?: number
    deductions?: string[]
  }
}

export interface AnalyticsSummary {
  device_id: string
  period_days: number
  daily: DailyConsumptionResponse
  averages: AverageConsumptionResponse
  usage_pattern: UsagePatternResponse
  peak_usage: PeakUsageResponse
  trend: ConsumptionTrendResponse
  leak_summary: LeakSummaryResponse
  efficiency: EfficiencyScoreResponse
}

export const analyticsService = {
  getAnalytics: async (deviceId: string, period = 'daily', limit = 30) => {
    const data = await analyticsService.getDailyConsumption(deviceId, limit)
    return data.records
  },

  getDailyConsumption: async (deviceId: string, days = 30): Promise<DailyConsumptionResponse> => {
    const { data } = await apiClient.get<DailyConsumptionResponse>(`/analytics/daily-consumption`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getWeeklyConsumption: async (deviceId: string, weeks = 4): Promise<WeeklyConsumptionResponse> => {
    const { data } = await apiClient.get<WeeklyConsumptionResponse>(`/analytics/weekly-consumption`, {
      params: { device_id: deviceId, weeks },
    })
    return data
  },

  getMonthlyConsumption: async (deviceId: string, months = 6): Promise<MonthlyConsumptionResponse> => {
    const { data } = await apiClient.get<MonthlyConsumptionResponse>(`/analytics/monthly-consumption`, {
      params: { device_id: deviceId, months },
    })
    return data
  },

  getAverageConsumption: async (deviceId: string, days = 30): Promise<AverageConsumptionResponse> => {
    const { data } = await apiClient.get<AverageConsumptionResponse>(`/analytics/average-consumption`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getUsagePattern: async (deviceId: string, days = 30): Promise<UsagePatternResponse> => {
    const { data } = await apiClient.get<UsagePatternResponse>(`/analytics/usage-pattern`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getPeakUsage: async (deviceId: string, days = 30): Promise<PeakUsageResponse> => {
    const { data } = await apiClient.get<PeakUsageResponse>(`/analytics/peak-usage`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getConsumptionTrend: async (deviceId: string, periodDays = 7): Promise<ConsumptionTrendResponse> => {
    const { data } = await apiClient.get<ConsumptionTrendResponse>(`/analytics/trend`, {
      params: { device_id: deviceId, period_days: periodDays },
    })
    return data
  },

  getLeakSummary: async (deviceId: string, days = 30): Promise<LeakSummaryResponse> => {
    const { data } = await apiClient.get<LeakSummaryResponse>(`/analytics/leak-events`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getEfficiencyScore: async (deviceId: string, days = 30): Promise<EfficiencyScoreResponse> => {
    const { data } = await apiClient.get<EfficiencyScoreResponse>(`/analytics/efficiency`, {
      params: { device_id: deviceId, days },
    })
    return data
  },

  getAnalyticsSummary: async (deviceId: string, days = 30): Promise<AnalyticsSummary> => {
    const { data } = await apiClient.get<AnalyticsSummary>(`/analytics/summary`, {
      params: { device_id: deviceId, days },
    })
    return data
  },
}
