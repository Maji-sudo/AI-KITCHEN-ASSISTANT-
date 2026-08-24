import type {
  User, Device, Cylinder, GasReading, WeightReading, LeakEvent,
  UsageAnalytics, RefillPrediction, Dish, CookingHistory,
  Recommendation, EfficiencyScore, Booking, Notification,
} from '@/types'

// ─── User ────────────────────────────────────────────────────────────────────
export const mockUser: User = {
  id: 1,
  name: 'Arjun Kumar',
  phone: '+919876543210',
  email: 'arjun@example.com',
  language_pref: 'en',
  created_at: '2026-01-15T10:00:00Z',
}

// ─── Devices ─────────────────────────────────────────────────────────────────
export const mockDevices: Device[] = [
  {
    id: 'SGD-001-ESP32',
    user_id: 1,
    name: 'Kitchen Sensor A',
    firmware_version: '1.2.4',
    status: 'active',
    paired_at: '2026-01-20T08:30:00Z',
    signal_strength: 87,
    battery_level: 92,
  },
  {
    id: 'SGD-002-ESP32',
    user_id: 1,
    name: 'Kitchen Sensor B',
    firmware_version: '1.2.3',
    status: 'offline',
    paired_at: '2026-02-10T11:00:00Z',
    signal_strength: 12,
    battery_level: 45,
  },
]

// ─── Cylinder ────────────────────────────────────────────────────────────────
export const mockCylinder: Cylinder = {
  id: 1,
  device_id: 'SGD-001-ESP32',
  tare_weight_g: 16200,
  full_weight_g: 30600,
  install_date: '2026-06-01T08:00:00Z',
  cylinder_type: '14.2kg',
  current_weight_g: 22150,
  percentage: 41,
}

// ─── Gas Readings ────────────────────────────────────────────────────────────
export const mockGasReadings: GasReading[] = Array.from({ length: 30 }, (_, i) => ({
  id: i + 1,
  device_id: 'SGD-001-ESP32',
  ppm_value: 80 + Math.random() * 120,
  status: 'safe' as const,
  timestamp: new Date(Date.now() - (30 - i) * 60000).toISOString(),
}))

export const mockCurrentPPM = 143.5

// ─── Leak Events ─────────────────────────────────────────────────────────────
export const mockLeakEvents: LeakEvent[] = [
  {
    id: 1,
    device_id: 'SGD-001-ESP32',
    start_time: '2026-07-28T14:23:00Z',
    end_time: '2026-07-28T14:27:00Z',
    peak_ppm: 1842,
    auto_shutoff_triggered: true,
    false_alarm: false,
  },
  {
    id: 2,
    device_id: 'SGD-001-ESP32',
    start_time: '2026-07-15T09:11:00Z',
    end_time: '2026-07-15T09:12:30Z',
    peak_ppm: 312,
    auto_shutoff_triggered: false,
    false_alarm: true,
  },
]

// ─── Analytics ───────────────────────────────────────────────────────────────
export const mockDailyAnalytics: UsageAnalytics[] = [
  { id: 1, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-07-28T00:00:00Z', consumption_g: 320, avg_rate: 13.3, anomaly_flag: false, forecast_next_g: 310 },
  { id: 2, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-07-29T00:00:00Z', consumption_g: 290, avg_rate: 12.1, anomaly_flag: false, forecast_next_g: 300 },
  { id: 3, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-07-30T00:00:00Z', consumption_g: 610, avg_rate: 25.4, anomaly_flag: true,  forecast_next_g: 350 },
  { id: 4, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-07-31T00:00:00Z', consumption_g: 280, avg_rate: 11.7, anomaly_flag: false, forecast_next_g: 290 },
  { id: 5, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-08-01T00:00:00Z', consumption_g: 305, avg_rate: 12.7, anomaly_flag: false, forecast_next_g: 300 },
  { id: 6, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-08-02T00:00:00Z', consumption_g: 270, avg_rate: 11.3, anomaly_flag: false, forecast_next_g: 285 },
  { id: 7, device_id: 'SGD-001-ESP32', period_type: 'daily', period_start: '2026-08-03T00:00:00Z', consumption_g: 195, avg_rate: 8.1, anomaly_flag: false, forecast_next_g: 280 },
]

export const mockWeeklyAnalytics: UsageAnalytics[] = [
  { id: 8,  device_id: 'SGD-001-ESP32', period_type: 'weekly', period_start: '2026-07-07T00:00:00Z', consumption_g: 2100, avg_rate: 12.5, anomaly_flag: false, forecast_next_g: 2200 },
  { id: 9,  device_id: 'SGD-001-ESP32', period_type: 'weekly', period_start: '2026-07-14T00:00:00Z', consumption_g: 1980, avg_rate: 11.8, anomaly_flag: false, forecast_next_g: 2050 },
  { id: 10, device_id: 'SGD-001-ESP32', period_type: 'weekly', period_start: '2026-07-21T00:00:00Z', consumption_g: 2350, avg_rate: 14.0, anomaly_flag: true,  forecast_next_g: 2100 },
  { id: 11, device_id: 'SGD-001-ESP32', period_type: 'weekly', period_start: '2026-07-28T00:00:00Z', consumption_g: 2070, avg_rate: 12.3, anomaly_flag: false, forecast_next_g: 2000 },
]

export const mockRefillPrediction: RefillPrediction = {
  id: 1,
  device_id: 'SGD-001-ESP32',
  predicted_empty_date: '2026-08-28T00:00:00Z',
  days_left: 25,
  confidence: 0.87,
  computed_at: '2026-08-03T06:00:00Z',
}

// ─── Dishes ───────────────────────────────────────────────────────────────────
export const mockDishes: Dish[] = [
  { id: 1, dish_name: 'Dal Tadka',       cuisine_tag: 'North Indian', base_gas_g: 45,  base_duration_min: 20 },
  { id: 2, dish_name: 'Rice (1 cup)',    cuisine_tag: 'Generic',      base_gas_g: 25,  base_duration_min: 15 },
  { id: 3, dish_name: 'Roti (6 pcs)',    cuisine_tag: 'North Indian', base_gas_g: 30,  base_duration_min: 12 },
  { id: 4, dish_name: 'Sambar',          cuisine_tag: 'South Indian', base_gas_g: 60,  base_duration_min: 30 },
  { id: 5, dish_name: 'Dosa (4 pcs)',    cuisine_tag: 'South Indian', base_gas_g: 35,  base_duration_min: 20 },
  { id: 6, dish_name: 'Egg Curry',       cuisine_tag: 'General',      base_gas_g: 55,  base_duration_min: 25 },
  { id: 7, dish_name: 'Chai (2 cups)',   cuisine_tag: 'Beverages',    base_gas_g: 18,  base_duration_min: 8  },
  { id: 8, dish_name: 'Paneer Butter Masala', cuisine_tag: 'North Indian', base_gas_g: 80, base_duration_min: 35 },
]

export const mockCookingHistory: CookingHistory[] = [
  { id: 1, user_id: 1, device_id: 'SGD-001-ESP32', dish_id: 1, dish: mockDishes[0], logged_date: '2026-08-03T07:30:00Z', actual_gas_g: 48, actual_duration_min: 22 },
  { id: 2, user_id: 1, device_id: 'SGD-001-ESP32', dish_id: 2, dish: mockDishes[1], logged_date: '2026-08-03T07:45:00Z', actual_gas_g: 26, actual_duration_min: 14 },
  { id: 3, user_id: 1, device_id: 'SGD-001-ESP32', dish_id: 3, dish: mockDishes[2], logged_date: '2026-08-02T19:00:00Z', actual_gas_g: 32, actual_duration_min: 15 },
  { id: 4, user_id: 1, device_id: 'SGD-001-ESP32', dish_id: 4, dish: mockDishes[3], logged_date: '2026-08-02T18:30:00Z', actual_gas_g: 65, actual_duration_min: 33 },
]

// ─── Recommendations ─────────────────────────────────────────────────────────
export const mockRecommendations: Recommendation[] = [
  {
    id: 1, user_id: 1, device_id: 'SGD-001-ESP32',
    category: 'efficiency',
    message: 'Your Tuesday cooking uses 2× more gas than similar households. Consider pressure cooking rice to save ~30g/day.',
    supporting_facts_json: { avg_consumption: 610, household_avg: 290, saving_potential: '30g/day', affected_dishes: ['Rice', 'Dal'] },
    confidence: 0.91, status: 'active',
  },
  {
    id: 2, user_id: 1, device_id: 'SGD-001-ESP32',
    category: 'refill',
    message: 'Your cylinder will be empty in approximately 25 days. Schedule a refill to avoid interruption.',
    supporting_facts_json: { days_left: 25, confidence: '87%', avg_daily_use: '305g' },
    confidence: 0.87, status: 'active',
  },
  {
    id: 3, user_id: 1, device_id: 'SGD-001-ESP32',
    category: 'safety',
    message: 'A gas leak was detected on Jul 28. Ensure your regulator valve is tightly closed after each use.',
    supporting_facts_json: { event_date: '2026-07-28', peak_ppm: 1842, duration_min: 4 },
    confidence: 0.98, status: 'active',
  },
  {
    id: 4, user_id: 1, device_id: 'SGD-001-ESP32',
    category: 'cooking',
    message: 'You cook Chai 3× daily. Using an insulated flask could save ~54g of gas per week.',
    supporting_facts_json: { dish: 'Chai', frequency: '3/day', weekly_savings: '54g' },
    confidence: 0.78, status: 'acted',
  },
  {
    id: 5, user_id: 1, device_id: 'SGD-001-ESP32',
    category: 'general',
    message: 'Your efficiency score improved by 8 points this week. Keep it up!',
    supporting_facts_json: { prev_score: 72, current_score: 80, delta: 8 },
    confidence: 1.0, status: 'active',
  },
]

// ─── Efficiency ───────────────────────────────────────────────────────────────
export const mockEfficiencyScore: EfficiencyScore = {
  id: 1,
  device_id: 'SGD-001-ESP32',
  period_type: 'weekly',
  overall_score: 78,
  component_scores_json: {
    safety: 85,
    gas_efficiency: 72,
    cooking_efficiency: 68,
    rec_compliance: 90,
    cylinder_utilization: 76,
  },
  computed_at: '2026-08-03T06:00:00Z',
}

export const mockEfficiencyHistory = [
  { week: 'Jun W4', score: 64 },
  { week: 'Jul W1', score: 69 },
  { week: 'Jul W2', score: 71 },
  { week: 'Jul W3', score: 70 },
  { week: 'Jul W4', score: 72 },
  { week: 'Aug W1', score: 78 },
]

// ─── Bookings ────────────────────────────────────────────────────────────────
export const mockBookings: Booking[] = [
  { id: 1, user_id: 1, device_id: 'SGD-001-ESP32', booking_date: '2026-06-01T10:00:00Z', distributor: 'HP Gas - Koramangala', status: 'delivered', source: 'app' },
  { id: 2, user_id: 1, device_id: 'SGD-001-ESP32', booking_date: '2026-08-25T10:00:00Z', distributor: 'HP Gas - Koramangala', status: 'pending',   source: 'auto' },
]

// ─── Notifications ────────────────────────────────────────────────────────────
export const mockNotifications: Notification[] = [
  { id: 1, user_id: 1, channel: 'fcm',      payload: { title: '🚨 Gas Leak Detected!',         body: 'Peak 1842 ppm at 2:23 PM. Auto shutoff triggered.',  category: 'safety'     }, sent_at: '2026-07-28T14:23:05Z', delivery_status: 'delivered', read: true  },
  { id: 2, user_id: 1, channel: 'fcm',      payload: { title: '⚠️ Cylinder Running Low',        body: 'Only 25 days of gas remaining. Book your refill now.', category: 'refill'     }, sent_at: '2026-08-03T08:00:00Z', delivery_status: 'delivered', read: false },
  { id: 3, user_id: 1, channel: 'whatsapp', payload: { title: '📊 Weekly Efficiency Report',    body: 'Your efficiency score is 78/100. View full report.',   category: 'efficiency' }, sent_at: '2026-08-03T07:00:00Z', delivery_status: 'delivered', read: false },
  { id: 4, user_id: 1, channel: 'sms',      payload: { title: '🍳 Cooking Tip',                 body: 'Use a pressure cooker to save 30g gas on rice daily.', category: 'cooking'    }, sent_at: '2026-08-02T12:00:00Z', delivery_status: 'delivered', read: true  },
  { id: 5, user_id: 1, channel: 'fcm',      payload: { title: '✅ Refill Booked Successfully',  body: 'Your refill from HP Gas Koramangala is confirmed.',    category: 'refill'     }, sent_at: '2026-08-01T09:30:00Z', delivery_status: 'delivered', read: true  },
]
