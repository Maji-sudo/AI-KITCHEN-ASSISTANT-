import { useState } from 'react'
import {
  BarChart3,
  Calendar,
  Download,
  Flame,
  AlertCircle,
  TrendingUp,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import { Card, StatCard } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { mockDailyAnalytics, mockWeeklyAnalytics } from '@/utils/mockData'
import { formatGrams } from '@/utils/cn'

export function Analytics() {
  const [period, setPeriod] = useState<'daily' | 'weekly'>('daily')

  const currentData = period === 'daily' ? mockDailyAnalytics : mockWeeklyAnalytics

  const chartData = currentData.map((d) => ({
    name: new Date(d.period_start).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
    }),
    Consumption: d.consumption_g,
    Forecast: d.forecast_next_g || d.consumption_g * 0.95,
    isAnomaly: d.anomaly_flag,
  }))

  const handleExportCSV = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,Period Start,Consumption (g),Avg Rate,Anomaly Flag\n' +
      currentData
        .map(
          (d) =>
            `${d.period_start},${d.consumption_g},${d.avg_rate},${d.anomaly_flag}`
        )
        .join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `safegas_analytics_${period}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center shrink-0">
            <BarChart3 className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Gas Consumption Analytics</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Track consumption trends, detect usage anomalies, and review forecast projections.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="bg-slate-100 dark:bg-slate-700 p-1 rounded-xl flex text-xs font-semibold">
            <button
              onClick={() => setPeriod('daily')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                period === 'daily' ? 'bg-white dark:bg-slate-800 text-primary shadow-xs' : 'text-slate-500'
              }`}
            >
              Daily
            </button>
            <button
              onClick={() => setPeriod('weekly')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                period === 'weekly' ? 'bg-white dark:bg-slate-800 text-primary shadow-xs' : 'text-slate-500'
              }`}
            >
              Weekly
            </button>
          </div>

          <Button variant="outline" size="sm" onClick={handleExportCSV} leftIcon={<Download className="h-4 w-4" />}>
            Export CSV
          </Button>
        </div>
      </div>

      {/* Grid Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Average Consumption"
          value={period === 'daily' ? '305 g / day' : '2,125 g / week'}
          subtitle="Household baseline target: 290 g/day"
          icon={<Flame className="h-5 w-5 text-amber-500" />}
          color="text-amber-500"
        />

        <StatCard
          title="Peak Gas Usage"
          value="610 g (Jul 30)"
          subtitle="Heavy cooking day (Dal + Paneer + Biryani)"
          icon={<TrendingUp className="h-5 w-5 text-red-500" />}
          color="text-red-500"
        />

        <StatCard
          title="Anomaly Incidents"
          value="1 Flagged"
          subtitle="Z-Score threshold &gt; 2.5 std dev"
          icon={<AlertCircle className="h-5 w-5 text-amber-500" />}
          color="text-amber-500"
        />
      </div>

      {/* Recharts Bar Chart Container */}
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <div>
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              {period === 'daily' ? 'Daily LPG Consumption (grams)' : 'Weekly Consumption Rollup'}
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <span className="h-3 w-3 rounded bg-primary" /> Actual Consumption
            </span>
            <span className="flex items-center gap-1">
              <span className="h-3 w-3 rounded bg-amber-400" /> AI Forecast
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
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                formatter={(val: any) => [`${val} g`, '']}
              />
              <Legend />
              <Bar dataKey="Consumption" fill="#16a34a" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Forecast" fill="#f59e0b" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Top Consuming Days Table */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Detailed Consumption Log & Anomaly Highlights
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-400 uppercase font-semibold">
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Consumption</th>
                <th className="py-2.5 px-3">Burn Rate (g/hr)</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
              {currentData.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                  <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-200">
                    {new Date(d.period_start).toLocaleDateString('en-IN', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">
                    {formatGrams(d.consumption_g)}
                  </td>
                  <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                    {d.avg_rate} g/hr
                  </td>
                  <td className="py-3 px-3">
                    {d.anomaly_flag ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 flex items-center gap-1 w-max">
                        <AlertCircle className="h-3 w-3" /> Anomaly Detected (+105% vs avg)
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400">
                        Normal Usage
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
