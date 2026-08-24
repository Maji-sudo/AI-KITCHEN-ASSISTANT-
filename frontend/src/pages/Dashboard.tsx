import { Link } from 'react-router-dom'
import {
  ShieldAlert,
  Flame,
  Zap,
  Sparkles,
  TrendingDown,
  Calendar,
  AlertTriangle,
  ArrowRight,
  Clock,
  Radio,
  PlusCircle,
  Bell,
} from 'lucide-react'
import { Card, StatCard } from '@/components/ui/Card'
import { Gauge } from '@/components/ui/Gauge'
import { Button } from '@/components/ui/Button'
import { categoryBadge, gasStatusBadge } from '@/components/ui/Badge'
import {
  mockCylinder,
  mockCurrentPPM,
  mockRefillPrediction,
  mockEfficiencyScore,
  mockRecommendations,
  mockNotifications,
  mockDailyAnalytics,
} from '@/utils/mockData'
import { formatGrams, formatPPM, getCylinderColor, getScoreColor } from '@/utils/cn'

export function Dashboard() {
  const todayConsumption = mockDailyAnalytics[mockDailyAnalytics.length - 1]?.consumption_g || 195
  const activeRecs = mockRecommendations.filter((r) => r.status === 'active')

  return (
    <div className="space-y-6">
      {/* Top Banner Alert if any warning */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0">
            <Radio className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-extrabold">All Kitchen Systems Operational</h2>
            <p className="text-xs text-green-100 mt-0.5">
              Live PPM: <strong>{formatPPM(mockCurrentPPM)}</strong> &bull; Cylinder Level: <strong>{mockCylinder.percentage}%</strong> ({mockRefillPrediction.days_left} days remaining)
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Link to="/safety">
            <Button size="sm" variant="secondary" className="bg-white/20 hover:bg-white/30 text-white border-0">
              Safety Live Monitor
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Safety Status"
          value={gasStatusBadge('safe')}
          subtitle={`Gas PPM: ${formatPPM(mockCurrentPPM)}`}
          icon={<ShieldAlert className="h-5 w-5 text-green-600 dark:text-green-400" />}
          color="text-green-600 dark:text-green-400"
        />

        <StatCard
          title="Today's Consumption"
          value={formatGrams(todayConsumption)}
          subtitle="Avg: 305g / day"
          icon={<Flame className="h-5 w-5 text-amber-500" />}
          color="text-amber-500"
          trend={{ value: -12, label: 'vs yesterday' }}
        />

        <StatCard
          title="Refill Prediction"
          value={`${mockRefillPrediction.days_left} Days`}
          subtitle={`Empty by ${new Date(mockRefillPrediction.predicted_empty_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}`}
          icon={<Calendar className="h-5 w-5 text-blue-500" />}
          color="text-blue-500"
        />

        <StatCard
          title="Efficiency Score"
          value={`${mockEfficiencyScore.overall_score} / 100`}
          subtitle="Top 15% of households"
          icon={<Zap className="h-5 w-5 text-primary" />}
          color="text-primary"
          trend={{ value: 8, label: 'this week' }}
        />
      </div>

      {/* Main Row: Gauges & Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cylinder Gauge Card */}
        <Card className="flex flex-col items-center justify-between text-center">
          <div className="w-full flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Flame className="h-4 w-4 text-amber-500" />
              Cylinder Capacity
            </h3>
            <Link to="/cylinder" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <Gauge
            value={mockCylinder.percentage || 41}
            size={160}
            strokeWidth={14}
            color={getCylinderColor(mockCylinder.percentage || 41)}
            label={`${mockCylinder.percentage}%`}
            sublabel={`${formatGrams(mockCylinder.current_weight_g || 22150)} remaining`}
          />

          <div className="w-full mt-6 grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-700/40 p-3 rounded-xl">
            <div>
              <span className="text-slate-400 block text-[10px]">Tare Weight</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">{formatGrams(mockCylinder.tare_weight_g)}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Full Weight</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">{formatGrams(mockCylinder.full_weight_g)}</span>
            </div>
          </div>

          <Link to="/cylinder" className="w-full mt-4">
            <Button className="w-full" size="sm">
              Book Refill Now
            </Button>
          </Link>
        </Card>

        {/* Efficiency Breakdown Card */}
        <Card className="flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              Efficiency Index
            </h3>
            <Link to="/efficiency" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              Score Breakdown <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="flex items-center justify-center my-2">
            <Gauge
              value={mockEfficiencyScore.overall_score}
              size={140}
              strokeWidth={12}
              color={getScoreColor(mockEfficiencyScore.overall_score)}
              label={`${mockEfficiencyScore.overall_score}`}
              sublabel="Overall Grade A"
            />
          </div>

          <div className="space-y-2 mt-4 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">Safety Compliance</span>
              <span className="font-bold text-slate-900 dark:text-white">85%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
              <div className="bg-green-500 h-full rounded-full" style={{ width: '85%' }} />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-600 dark:text-slate-400">Gas Usage Efficiency</span>
              <span className="font-bold text-slate-900 dark:text-white">72%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-full rounded-full" style={{ width: '72%' }} />
            </div>
          </div>
        </Card>

        {/* Quick Actions & AI Insights */}
        <Card className="flex flex-col justify-between">
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Quick Actions & Tools
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <Link to="/cooking" className="p-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary transition-colors flex flex-col items-center text-center gap-1.5">
              <PlusCircle className="h-6 w-6" />
              <span className="text-xs font-bold">Log Cooking</span>
            </Link>
            <Link to="/cooking" className="p-3 rounded-xl bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/30 dark:hover:bg-blue-900/40 text-blue-600 dark:text-blue-400 transition-colors flex flex-col items-center text-center gap-1.5">
              <Sparkles className="h-6 w-6" />
              <span className="text-xs font-bold">AI Assistant</span>
            </Link>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700">
            <p className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5 mb-1">
              <TrendingDown className="h-4 w-4 text-green-500" />
              Gas Saving Tip
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
              Soaking rice for 30 mins before cooking can reduce gas consumption by up to 20%.
            </p>
          </div>
        </Card>
      </div>

      {/* Lower Row: Recommendations & Recent Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Recommendations (2 Cols) */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Active Recommendations ({activeRecs.length})
            </h3>
            <Link to="/recommendations" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {activeRecs.slice(0, 3).map((rec) => (
              <div
                key={rec.id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700/80 flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {categoryBadge(rec.category)}
                    <span className="text-[10px] font-bold text-slate-400">
                      {Math.round(rec.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-200 font-medium">{rec.message}</p>
                </div>
                <Link to="/recommendations">
                  <Button size="sm" variant="outline" className="text-xs h-8 shrink-0">
                    Review
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </Card>

        {/* Notifications Digest (1 Col) */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Bell className="h-4 w-4 text-blue-500" />
              Recent Alerts
            </h3>
            <Link to="/notifications" className="text-xs font-semibold text-primary hover:underline">
              All
            </Link>
          </div>

          <div className="space-y-3">
            {mockNotifications.slice(0, 3).map((n) => (
              <div key={n.id} className="flex items-start gap-2.5 text-xs border-b border-slate-100 dark:border-slate-700/50 pb-2.5 last:border-0 last:pb-0">
                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">{n.payload.title}</p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">{n.payload.body}</p>
                  <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
                    <Clock className="h-3 w-3" />
                    {new Date(n.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
