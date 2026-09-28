// ─── Auth ────────────────────────────────────────────────────────────────────
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface OTPRequestPayload { phone: string }
export interface OTPVerifyPayload  { phone: string; otp: string }

// ─── User ────────────────────────────────────────────────────────────────────
export interface User {
  id: number
  name: string
  phone: string
  email?: string
  language_pref: 'en' | 'hi' | 'ta'
  created_at: string
}

// ─── Device ──────────────────────────────────────────────────────────────────
export type DeviceStatus = 'active' | 'inactive' | 'offline' | 'error'

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
export type GasStatus = 'normal' | 'warning' | 'critical' | 'safe' | 'danger'

export interface GasReading {
  id: number
  device_id: string
  ppm_value: number
  status: string
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
  notification_id?: number | null
}

// ─── Safety & Diagnostics (Phase 7-9) ───────────────────────────────────────
export interface SafetyStatusResponse {
  device_id: string
  latest_gas_ppm?: number | null
  timestamp?: string | null
  status?: string | null  // normal | warning | critical
  valve_status?: string | null // OPEN | CLOSED
  connection_status?: string | null // online | offline | unknown
  last_seen?: string | null
}

export interface ActiveLeakResponse {
  id: number
  device_id: string
  start_time: string
  end_time?: string | null
  peak_ppm: number
  auto_shutoff_triggered?: boolean
  false_alarm?: boolean
  notification_id?: number | null
  active: boolean
}

export interface LeakHistoryResponse {
  leaks: ActiveLeakResponse[]
}

export interface DiagnosticDeviceNode {
  id: string
  name: string
  paired: boolean
}

export interface DiagnosticConnectionNode {
  status: string
  last_seen?: string | null
}

export interface DiagnosticSensorNode {
  health: string
  battery_level?: number | null
  signal_strength?: number | null
  last_calibrated_at?: string | null
}

export interface DiagnosticTelemetryNode {
  latest_gas_ppm?: number | null
  timestamp?: string | null
  source?: string | null
}

export interface DiagnosticSafetyNode {
  valve_status: string
}

export interface DeviceDiagnosticsResponse {
  device: DiagnosticDeviceNode
  connection: DiagnosticConnectionNode
  sensor: DiagnosticSensorNode
  telemetry: DiagnosticTelemetryNode
  safety: DiagnosticSafetyNode
}

export interface SimulatorStartRequest {
  device_id: string
  baseline_ppm?: number
  interval_seconds?: number
  count?: number
  mode?: string
}

export interface SimulatorStatusResponse {
  device_id: string
  running: boolean
  generated_count: number
  baseline_ppm?: number | null
  last_ppm?: number | null
  interval_seconds?: number | null
  mode?: string | null
}


// ─── Analytics ───────────────────────────────────────────────────────────────
export type PeriodType = 'daily' | 'weekly' | 'monthly'

export interface UsageAnalytics {
  id: number
  device_id: string
  period_type: PeriodType
  period_start: string
  consumption_g: number
  avg_rate: number
  anomaly_flag: boolean
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
  status: RecommendationStatus
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
