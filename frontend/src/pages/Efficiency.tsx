import { useState } from 'react'
import {
  Zap,
  TrendingUp,
  ShieldCheck,
  Flame,
  ChefHat,
  Sparkles,
  Award,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { Card, StatCard } from '@/components/ui/Card'
import { Gauge } from '@/components/ui/Gauge'
import { mockEfficiencyScore, mockEfficiencyHistory } from '@/utils/mockData'
import { getScoreColor } from '@/utils/cn'

export function Efficiency() {
  const [period] = useState<'weekly' | 'monthly'>('weekly')
  const { overall_score, component_scores_json } = mockEfficiencyScore

  const components = [
    {
      name: 'Safety Score',
      weight: '30%',
      score: component_scores_json.safety,
      icon: ShieldCheck,
      color: 'bg-green-500',
      desc: 'Zero leak triggers & verified valve shutoffs',
    },
    {
      name: 'Gas Usage Efficiency',
      weight: '25%',
      score: component_scores_json.gas_efficiency,
      icon: Flame,
      color: 'bg-amber-500',
      desc: 'Daily burn rate vs benchmark household',
    },
    {
      name: 'Recommendation Compliance',
      weight: '20%',
      score: component_scores_json.rec_compliance,
      icon: Sparkles,
      color: 'bg-blue-500',
      desc: 'Accepted and acted recommendation ratio',
    },
    {
      name: 'Cooking Efficiency',
      weight: '15%',
      score: component_scores_json.cooking_efficiency,
      icon: ChefHat,
      color: 'bg-primary',
      desc: 'Actual cook times vs dish library benchmarks',
    },
    {
      name: 'Cylinder Utilization',
      weight: '10%',
      score: component_scores_json.cylinder_utilization,
      icon: Award,
      color: 'bg-purple-500',
      desc: 'Residual gas remaining at cylinder changeout',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Smart Kitchen Efficiency Score</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Comprehensive 5-component weighted score algorithm.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Large Gauge & Component Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Gauge Card */}
        <Card className="flex flex-col items-center justify-center text-center p-8">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-6">
            Overall Efficiency Grade
          </h3>

          <Gauge
            value={overall_score}
            size={220}
            strokeWidth={18}
            color={getScoreColor(overall_score)}
            label={`${overall_score}`}
            sublabel="Grade A (Top 15%)"
          />

          <div className="mt-6 p-3 rounded-xl bg-green-50 dark:bg-green-950/40 text-green-700 dark:text-green-400 text-xs font-bold flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            <span>+8 points improvement from last week</span>
          </div>
        </Card>

        {/* 5-Component Breakdown Bars (2 Cols) */}
        <Card className="lg:col-span-2">
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              5-Component Weighted Breakdown
            </h3>
          </div>

          <div className="space-y-4">
            {components.map((c) => {
              const Icon = c.icon
              return (
                <div key={c.name} className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                      <Icon className="h-4 w-4 text-slate-400" />
                      {c.name}
                      <span className="text-[10px] text-slate-400 font-normal">({c.weight} weight)</span>
                    </span>
                    <span className="font-extrabold text-slate-900 dark:text-white">{c.score} / 100</span>
                  </div>

                  <div className="w-full bg-slate-100 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${c.color}`}
                      style={{ width: `${c.score}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">{c.desc}</p>
                </div>
              )
            })}
          </div>
        </Card>
      </div>

      {/* Weekly Trend Chart & Delta Explanations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Weekly Efficiency Score Trend
            </h3>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockEfficiencyHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[50, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  formatter={(val: any) => [`${val} pts`, 'Score']}
                />
                <Line type="monotone" dataKey="score" stroke="#16a34a" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Delta Explanation Card */}
        <Card>
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              AI Delta Explanations
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-green-50 dark:bg-green-950/40 text-green-800 dark:text-green-300">
              <p className="font-bold">+5 pts: Recommendation Compliance</p>
              <p className="text-[11px] mt-0.5 text-green-700 dark:text-green-400">
                You accepted 3 efficiency recommendations this week!
              </p>
            </div>

            <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300">
              <p className="font-bold">+3 pts: Gas Efficiency</p>
              <p className="text-[11px] mt-0.5 text-blue-700 dark:text-blue-400">
                Average daily burn rate dropped from 320g to 305g.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
