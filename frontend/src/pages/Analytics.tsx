import { useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  Calendar,
  Flame,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  ShieldCheck,
  RefreshCw,
  Clock,
  Award,
  Zap,
  CheckCircle2,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts'
import { Card, StatCard } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { analyticsService, type AnalyticsSummary } from '@/services/analytics.service'
import { deviceService } from '@/services/device.service'
import type { Device } from '@/types'
import { formatGrams } from '@/utils/cn'

export function Analytics() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [days, setDays] = useState<number>(30)

  const [data, setData] = useState<AnalyticsSummary | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  // Fetch devices on mount
  useEffect(() => {
    async function loadDevices() {
      try {
        const list = await deviceService.getDevices()
        setDevices(list)
        if (list.length > 0) {
          setSelectedDeviceId(list[0].id)
        }
      } catch (err: any) {
        console.error('Failed to load devices:', err)
      }
    }
    loadDevices()
  }, [])

  // Fetch analytics summary whenever selectedDeviceId or days changes
  const fetchAnalytics = useCallback(async () => {
    if (!selectedDeviceId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const summary = await analyticsService.getAnalyticsSummary(selectedDeviceId, days)
      setData(summary)
    } catch (err: any) {
      console.error('Failed to fetch analytics summary:', err)
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to load analytics telemetry. Please check backend server.'
      )
    } finally {
      setIsLoading(false)
    }
  }, [selectedDeviceId, days])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  const handlePeriodChange = (newPeriod: 'daily' | 'weekly' | 'monthly') => {
    setPeriod(newPeriod)
    if (newPeriod === 'daily') setDays(30)
    else if (newPeriod === 'weekly') setDays(28)
    else if (newPeriod === 'monthly') setDays(90)
  }

  // Build Recharts data depending on selected period
  const getChartData = () => {
    if (!data) return []

    if (period === 'daily') {
      return data.daily.records.map((r) => ({
        name: new Date(r.date).toLocaleDateString('en-IN', {
          month: 'short',
          day: 'numeric',
        }),
        Consumption: r.consumption_g,
        ConsumptionKg: r.consumption_kg,
      }))
    } else if (period === 'weekly') {
      const weeklyRes = data.daily.records
      const weeksData = []
      for (let i = 0; i < weeklyRes.length; i += 7) {
        const chunk = weeklyRes.slice(i, i + 7)
        const sumG = chunk.reduce((acc, c) => acc + c.consumption_g, 0)
        weeksData.push({
          name: `W${Math.floor(i / 7) + 1} (${chunk[0]?.date.slice(5)})`,
          Consumption: Math.round(sumG),
          ConsumptionKg: Math.round((sumG / 1000) * 100) / 100,
        })
      }
      return weeksData
    } else {
      const monthlyMap: Record<string, number> = {}
      data.daily.records.forEach((r) => {
        const mKey = r.date.slice(0, 7) // YYYY-MM
        monthlyMap[mKey] = (monthlyMap[mKey] || 0) + r.consumption_g
      })
      return Object.entries(monthlyMap).map(([mKey, sumG]) => {
        const [y, m] = mKey.split('-')
        const label = new Date(parseInt(y), parseInt(m) - 1, 1).toLocaleDateString('en-IN', {
          month: 'short',
        })
        return {
          name: label,
          Consumption: Math.round(sumG),
          ConsumptionKg: Math.round((sumG / 1000) * 100) / 100,
        }
      })
    }
  }

  const chartData = getChartData()

  const patternSlotColors: Record<string, string> = {
    Morning: '#f59e0b',   // Amber
    Afternoon: '#3b82f6', // Blue
    Evening: '#16a34a',   // Green
    Night: '#8b5cf6',     // Purple
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Device / Period Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center shrink-0">
            <BarChart3 className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Gas Consumption Analytics</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Decoupled historical LPG analysis, time-of-day usage patterns & efficiency scoring.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Device Selector */}
          {devices.length > 0 && (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="h-9 px-3 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-600 focus:outline-none"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.id})
                </option>
              ))}
            </select>
          )}

          {/* Period Toggle */}
          <div className="bg-slate-100 dark:bg-slate-700 p-1 rounded-xl flex text-xs font-semibold">
            <button
              onClick={() => handlePeriodChange('daily')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                period === 'daily' ? 'bg-white dark:bg-slate-800 text-primary shadow-xs' : 'text-slate-500'
              }`}
            >
              Daily
            </button>
            <button
              onClick={() => handlePeriodChange('weekly')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                period === 'weekly' ? 'bg-white dark:bg-slate-800 text-primary shadow-xs' : 'text-slate-500'
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => handlePeriodChange('monthly')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                period === 'monthly' ? 'bg-white dark:bg-slate-800 text-primary shadow-xs' : 'text-slate-500'
              }`}
            >
              Monthly
            </button>
          </div>

          <Button variant="outline" size="sm" onClick={fetchAnalytics} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <Card className="py-16 text-center">
          <div className="h-8 w-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Analyzing LPG telemetry data & calculating metrics...
          </p>
        </Card>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <Card className="border-red-200 dark:border-red-900/50 bg-red-50/40 dark:bg-red-950/20 text-center py-8">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm font-bold text-red-600 dark:text-red-400 mb-1">{error}</p>
          <p className="text-xs text-slate-500 mb-4">Make sure backend is running and synthetic telemetry is generated.</p>
          <Button size="sm" onClick={fetchAnalytics}>
            Retry Fetching Analytics
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && !data && (
        <Card className="py-16 text-center">
          <Flame className="h-10 w-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-700 dark:text-slate-300">No Telemetry Readings Found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            No active LPG cylinder weight readings exist for device {selectedDeviceId}. Run the synthetic generator script to populate test data.
          </p>
        </Card>
      )}

      {/* Main Analytics Content */}
      {!isLoading && !error && data && (
        <>
          {/* Key Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Consumption"
              value={`${data.daily.total_consumption_kg} kg`}
              subtitle={`${data.daily.total_consumption_g.toLocaleString()} g over past ${days} days`}
              icon={<Flame className="h-5 w-5 text-amber-500" />}
              color="text-amber-500"
            />

            <StatCard
              title="Average Daily Rate"
              value={`${data.averages.avg_daily_g} g / day`}
              subtitle={`Weekly avg: ${data.averages.avg_weekly_kg} kg / week`}
              icon={<Activity className="h-5 w-5 text-blue-500" />}
              color="text-blue-500"
            />

            <StatCard
              title="Consumption Trend"
              value={data.trend.trend.toUpperCase()}
              subtitle={data.trend.description}
              icon={
                data.trend.trend === 'increasing' ? (
                  <TrendingUp className="h-5 w-5 text-red-500" />
                ) : data.trend.trend === 'decreasing' ? (
                  <TrendingDown className="h-5 w-5 text-green-500" />
                ) : (
                  <Activity className="h-5 w-5 text-blue-500" />
                )
              }
              color={
                data.trend.trend === 'increasing'
                  ? 'text-red-500'
                  : data.trend.trend === 'decreasing'
                  ? 'text-green-500'
                  : 'text-blue-500'
              }
            />

            <StatCard
              title="Efficiency Score"
              value={`${data.efficiency.overall_score} / 100`}
              subtitle={`Grade ${data.efficiency.grade} • Deterministic rule-based`}
              icon={<Award className="h-5 w-5 text-emerald-500" />}
              color="text-emerald-500"
            />
          </div>

          {/* Consumption Chart Container */}
          <Card>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4 gap-2">
              <div>
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-primary" />
                  {period === 'daily'
                    ? `Daily LPG Consumption (past ${days} days)`
                    : period === 'weekly'
                    ? 'Weekly LPG Consumption Rollup'
                    : 'Monthly LPG Consumption Aggregation'}
                </h3>
              </div>

              <div className="flex items-center gap-3 text-xs font-medium text-slate-500">
                <span className="flex items-center gap-1.5">
                  <span className="h-3 w-3 rounded bg-primary" /> Net Weight Decrease (Grams)
                </span>
              </div>
            </div>

            <div className="h-80 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                    formatter={(val: any) => [`${val} g (${(Number(val) / 1000).toFixed(2)} kg)`, 'Consumption']}
                  />
                  <Bar dataKey="Consumption" fill="#16a34a" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Usage Pattern & Rule-Based Efficiency Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Time-of-Day Usage Pattern */}
            <Card>
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-500" /> Usage Pattern (Time of Day)
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-400">
                  Peak: {data.usage_pattern.peak_period}
                </span>
              </div>

              <div className="space-y-4">
                {data.usage_pattern.slots.map((slot) => (
                  <div key={slot.slot_name} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: patternSlotColors[slot.slot_name] || '#64748b' }}
                        />
                        <span className="font-bold text-slate-800 dark:text-slate-200">{slot.slot_name}</span>
                        <span className="text-slate-400 text-[11px]">({slot.time_range})</span>
                      </div>
                      <span className="font-bold text-slate-900 dark:text-white">
                        {slot.consumption_g.toLocaleString()} g ({slot.percentage}%)
                      </span>
                    </div>

                    <div className="h-2.5 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${slot.percentage}%`,
                          backgroundColor: patternSlotColors[slot.slot_name] || '#3b82f6',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Rule-Based Kitchen Efficiency Details */}
            <Card>
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Zap className="h-4 w-4 text-emerald-500" /> Rule-Based Kitchen Efficiency Engine
                </h3>
                <span className="px-2.5 py-1 rounded-xl text-xs font-black bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400">
                  {data.efficiency.overall_score} / 100 ({data.efficiency.grade})
                </span>
              </div>

              <div className="space-y-3">
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                  {data.efficiency.explanation}
                </p>

                <div className="space-y-2 pt-1">
                  <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Scoring Components</h4>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700">
                      <span className="text-slate-400 block text-[10px]">Safety Subscore</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {data.efficiency.components_json.safety_score ?? 100} / 100
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700">
                      <span className="text-slate-400 block text-[10px]">Consistency Subscore</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {data.efficiency.components_json.consumption_consistency ?? 100} / 100
                      </span>
                    </div>
                  </div>

                  {data.efficiency.components_json.deductions && data.efficiency.components_json.deductions.length > 0 && (
                    <div className="mt-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs">
                      <span className="font-bold text-amber-500 block mb-1">Deduction Rules Applied:</span>
                      <ul className="list-disc list-inside text-slate-600 dark:text-slate-300 space-y-0.5 text-[11px]">
                        {data.efficiency.components_json.deductions.map((d, idx) => (
                          <li key={idx}>{d}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* Leak Events Summary Card */}
          <Card>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" /> Leak & Safety Audit Log
              </h3>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-400">
                  Total Leaks: <strong className="text-slate-800 dark:text-slate-200">{data.leak_summary.total_leaks}</strong>
                </span>
                <span className="text-slate-400">
                  Peak Gas PPM: <strong className="text-slate-800 dark:text-slate-200">{data.leak_summary.peak_ppm} PPM</strong>
                </span>
              </div>
            </div>

            {data.leak_summary.recent_events.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                No gas leak events recorded in past {days} days. System status normal.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-400 uppercase font-semibold">
                      <th className="py-2.5 px-3">Date & Time</th>
                      <th className="py-2.5 px-3">Peak PPM</th>
                      <th className="py-2.5 px-3">Auto Shutoff Triggered</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                    {data.leak_summary.recent_events.map((e) => (
                      <tr key={e.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                        <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-200">
                          {new Date(e.start_time).toLocaleString('en-IN', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </td>
                        <td className="py-3 px-3 font-bold text-red-500">{e.peak_ppm} PPM</td>
                        <td className="py-3 px-3">
                          {e.auto_shutoff_triggered ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400">
                              Valve Closed
                            </span>
                          ) : (
                            <span className="text-slate-400">Manual</span>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400">
                            Gas Warning Triggered
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* Detailed Daily Log Table */}
          <Card>
            <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Detailed Daily Consumption Log
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-400 uppercase font-semibold">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Consumption (g)</th>
                    <th className="py-2.5 px-3">Consumption (kg)</th>
                    <th className="py-2.5 px-3">Drop Events Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {data.daily.records.map((d) => (
                    <tr key={d.date} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                      <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-200">
                        {new Date(d.date).toLocaleDateString('en-IN', {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">
                        {formatGrams(d.consumption_g)}
                      </td>
                      <td className="py-3 px-3 text-slate-600 dark:text-slate-300 font-semibold">
                        {d.consumption_kg} kg
                      </td>
                      <td className="py-3 px-3 text-slate-500">{d.reading_count} drops recorded</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
