// ─── Auth ────────────────────────────────────────────────────────────────────
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// ─── User ────────────────────────────────────────────────────────────────────
export interface User {
  id: number
  name: string
  phone?: string | null
  email?: string
  language_pref: 'en' | 'hi' | 'ta'
  created_at: string
}


// ─── Device ──────────────────────────────────────────────────────────────────
export type DeviceStatus = 'active' | 'inactive' | 'online' | 'offline' | 'error' | 'connected' | 'disconnected' | (string & {})

export interface Device {
  id: string
  user_id: number
  name: string
  firmware_version: string
  status: DeviceStatus
  paired_at: string
  signal_strength?: number   // 0-100
  battery_level?: number     // 0-100
}

// ─── Cylinder ────────────────────────────────────────────────────────────────
export interface Cylinder {
  id: number
  device_id: string
  tare_weight_g: number
  full_weight_g: number
  install_date: string
  cylinder_type: string
  current_weight_g?: number
  percentage?: number
}

// ─── Telemetry ───────────────────────────────────────────────────────────────
export type GasStatus = 'safe' | 'warning' | 'danger' | 'critical' | 'normal'

export interface GasReading {
  id: number
  device_id: string
  ppm_value: number
  status: GasStatus
  timestamp: string
  source?: string
}

export interface WeightReading {
  id: number
  device_id: string
  weight_g: number
  timestamp: string
}

export interface LeakEvent {
  id: number
  device_id: string
  start_time: string
  end_time?: string
  peak_ppm: number
  auto_shutoff_triggered: boolean
  false_alarm: boolean
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export type PeriodType = 'daily' | 'weekly' | 'monthly'

export interface UsageAnalytics {
  id: number
  device_id: string
  period_type: PeriodType
  period_start: string
  consumption_g?: number
  total_consumption_g?: number
  avg_rate?: number
  anomaly_flag?: boolean
  forecast_next_g?: number
}


export interface RefillPrediction {
  id: number
  device_id: string
  predicted_empty_date: string
  days_left: number
  confidence: number
  computed_at: string
}

// ─── Cooking ─────────────────────────────────────────────────────────────────
export interface Dish {
  id: number
  dish_name: string
  cuisine_tag: string
  base_gas_g: number
  base_duration_min: number
}

export interface CookingHistory {
  id: number
  user_id: number
  device_id: string
  dish_id?: number
  dish?: Dish
  logged_date: string
  actual_gas_g?: number
  actual_duration_min?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

// ─── Recommendations ─────────────────────────────────────────────────────────
export type RecommendationCategory = 'safety' | 'efficiency' | 'cooking' | 'refill' | 'general'
export type RecommendationStatus = 'active' | 'acted' | 'dismissed'

export interface Recommendation {
  id: number
  user_id: number
  device_id: string
  category: RecommendationCategory
  message: string
  supporting_facts_json?: Record<string, unknown>
  confidence: number
  /** 1=critical | 2=high | 3=medium | 4=low */
  priority: number
  status: RecommendationStatus
  created_at?: string
}

export interface RecommendationCounts {
  active: number
  acted: number
  dismissed: number
}

export interface GenerateResponse {
  device_id: string
  generated: number
  rules_triggered: string[]
  message: string
}

// ─── Efficiency ───────────────────────────────────────────────────────────────
export interface ComponentScores {
  safety: number
  gas_efficiency: number
  cooking_efficiency: number
  rec_compliance: number
  cylinder_utilization: number
}

export interface EfficiencyScore {
  id: number
  device_id: string
  period_type: 'weekly' | 'monthly'
  overall_score: number
  component_scores_json: ComponentScores
  computed_at: string
}

// ─── Booking ──────────────────────────────────────────────────────────────────
export type BookingStatus = 'pending' | 'confirmed' | 'delivered' | 'cancelled'
export type BookingSource = 'app' | 'manual' | 'auto'

export interface Booking {
  id: number
  user_id: number
  device_id: string
  booking_date: string
  distributor: string
  status: BookingStatus
  source: BookingSource
}

// ─── Notifications ────────────────────────────────────────────────────────────
export type NotificationChannel = 'fcm' | 'sms' | 'whatsapp'
export type DeliveryStatus = 'pending' | 'sent' | 'delivered' | 'failed'

export interface Notification {
  id: number
  user_id: number
  channel: NotificationChannel
  payload: {
    title: string
    body: string
    category?: string
  }
  sent_at: string
  delivery_status: DeliveryStatus
  read?: boolean
}

// ─── API Responses ────────────────────────────────────────────────────────────
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ─── Safety API Responses ──────────────────────────────────────────────────
export interface SafetyStatusResponse {
  device_id: string
  latest_gas_ppm: number | null
  timestamp?: string | null
  status: GasStatus | null
  valve_status: 'OPEN' | 'CLOSED' | 'unknown'
  connection_status: 'online' | 'offline' | 'unknown'
  last_seen: string | null
  source?: string | null
}

export interface ActiveLeakResponse {
  device_id: string
  start_time: string
  peak_ppm: number
  active: boolean
  end_time: string | null
}

export interface LeakHistoryResponse {
  leaks: LeakEvent[]
}

export interface DeviceDiagnosticsResponse {
  device: {
    id: string
    name: string
    firmware: string
    paired: boolean
  }
  connection: {
    status: 'online' | 'offline' | 'unknown'
    signal_strength: number | null
    last_seen: string | null
  }
  sensor: {
    health: 'healthy' | 'unknown' | 'degraded' | 'fault'
    calibration_date: string | null
    battery_level: number | null
  }
  telemetry: {
    latest_gas_ppm: number | null
    latest_weight_g: number | null
  }
  safety: {
    valve_status: 'OPEN' | 'CLOSED' | 'unknown'
    active_leak: boolean
  }
}

export interface SimulatorStartRequest {
  device_id: string
  scenario?: string
}

export interface SimulatorStatusResponse {
  device_id: string
  running: boolean
  scenario: string
  elapsed_seconds: number
  current_ppm: number
  current_status: string
}

// ─── Gas Agencies (Nearby Finder) ───────────────────────────────────────────
export interface GasAgency {
  id: string
  name: string
  address: string
  latitude: number
  longitude: number
  distance_km: number
  phone_number?: string | null
  google_maps_url: string
  rating?: number | null
  user_ratings_total?: number | null
}

export interface GasAgenciesResponse {
  success: boolean
  count: number
  radius_meters: number
  user_location?: {
    latitude: number
    longitude: number
  } | null
  agencies: GasAgency[]
  message?: string | null
}

