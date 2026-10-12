import { useState, useEffect, useCallback } from 'react'
import {
  Sparkles,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  Zap,
  ChefHat,
  Flame,
  Info,
  Cpu,
} from 'lucide-react'
import { Card, StatCard } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { categoryBadge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Loader'
import { EmptyState } from '@/components/ui/StateViews'
import { recommendationService } from '@/services/recommendation.service'
import { deviceService } from '@/services/device.service'
import type {
  Recommendation,
  RecommendationCategory,
  RecommendationCounts,
  Device,
} from '@/types'

// ─── Priority helpers ─────────────────────────────────────────────────────────

const PRIORITY_LABEL: Record<number, string> = {
  1: 'Critical',
  2: 'High',
  3: 'Medium',
  4: 'Low',
}

const PRIORITY_COLORS: Record<number, string> = {
  1: 'bg-red-100 dark:bg-red-950/40 text-red-600 dark:text-red-400',
  2: 'bg-amber-100 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400',
  3: 'bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400',
  4: 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300',
}

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  safety:     ShieldAlert,
  efficiency: Zap,
  cooking:    ChefHat,
  refill:     Flame,
  general:    Info,
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function Recommendations() {
  // Device selector
  const [devices, setDevices]           = useState<Device[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')

  // Recommendations data
  const [recs, setRecs]                 = useState<Recommendation[]>([])
  const [counts, setCounts]             = useState<RecommendationCounts>({ active: 0, acted: 0, dismissed: 0 })
  const [isLoading, setIsLoading]       = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError]               = useState('')
  const [generateMsg, setGenerateMsg]   = useState('')

  // Filters / UI state
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter]     = useState<'active' | 'all'>('active')
  const [searchQuery, setSearchQuery]       = useState('')
  const [expandedId, setExpandedId]         = useState<number | null>(null)

  // ── Load devices on mount ───────────────────────────────────────────────────
  useEffect(() => {
    deviceService.getDevices().then((list) => {
      setDevices(list)
      if (list.length > 0) setSelectedDeviceId(list[0].id)
    }).catch(() => setError('Failed to load devices.'))
  }, [])

  // ── Fetch recommendations ───────────────────────────────────────────────────
  const fetchRecommendations = useCallback(async () => {
    if (!selectedDeviceId) { setIsLoading(false); return }
    setIsLoading(true)
    setError('')
    try {
      const [data, countData] = await Promise.all([
        recommendationService.getRecommendations(0, 100, statusFilter === 'all'),
        recommendationService.getCounts(),
      ])
      setRecs(data)
      setCounts(countData)
    } catch {
      setError('Failed to load recommendations. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedDeviceId, statusFilter])

  useEffect(() => { fetchRecommendations() }, [fetchRecommendations])

  // ── Generate (call rule engine) ─────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!selectedDeviceId || isGenerating) return
    setIsGenerating(true)
    setGenerateMsg('')
    setError('')
    try {
      const res = await recommendationService.generate(selectedDeviceId, 30)
      setGenerateMsg(res.message)
      await fetchRecommendations()
    } catch {
      setError('Failed to generate recommendations. Ensure your device has telemetry data.')
    } finally {
      setIsGenerating(false)
    }
  }

  // ── Status transitions ──────────────────────────────────────────────────────
  const handleAct = async (id: number) => {
    try {
      const updated = await recommendationService.act(id)
      setRecs((prev) => prev.map((r) => (r.id === id ? updated : r)))
      setCounts((c) => ({ ...c, active: Math.max(0, c.active - 1), acted: c.acted + 1 }))
    } catch { /* silently ignore for UX */ }
  }

  const handleDismiss = async (id: number) => {
    try {
      const updated = await recommendationService.dismiss(id)
      setRecs((prev) => prev.map((r) => (r.id === id ? updated : r)))
      setCounts((c) => ({ ...c, active: Math.max(0, c.active - 1), dismissed: c.dismissed + 1 }))
    } catch { /* silently ignore for UX */ }
  }

  // ── Filtered view ───────────────────────────────────────────────────────────
  const filteredRecs = recs.filter((r) => {
    const matchesCat    = categoryFilter === 'all' || r.category === categoryFilter
    const matchesSearch = r.message.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter
    return matchesCat && matchesSearch && matchesStatus
  })

  // ── Category tabs ───────────────────────────────────────────────────────────
  const categories = [
    { label: 'All',        value: 'all' },
    { label: '🛡️ Safety',    value: 'safety' },
    { label: '⚡ Efficiency', value: 'efficiency' },
    { label: '🍳 Cooking',   value: 'cooking' },
    { label: '🔋 Refill',    value: 'refill' },
    { label: 'ℹ️ General',   value: 'general' },
  ]

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">

      {/* ── Header Banner ────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-amber-100 dark:bg-amber-950/40 text-amber-500 flex items-center justify-center shrink-0">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">
              AI Recommendations Engine
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Personalised LPG-saving strategies backed by your live telemetry data.
            </p>
          </div>
        </div>

        {/* Device selector + Refresh button */}
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          {devices.length > 1 && (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.id})</option>
              ))}
            </select>
          )}
          {devices.length === 1 && (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <Cpu className="h-3.5 w-3.5" />
              <span>{devices[0].name}</span>
            </div>
          )}
          <Button
            size="sm"
            variant="primary"
            onClick={handleGenerate}
            disabled={isGenerating || !selectedDeviceId}
            leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isGenerating ? 'animate-spin' : ''}`} />}
          >
            {isGenerating ? 'Analysing…' : 'Refresh Insights'}
          </Button>
        </div>
      </div>

      {/* ── Generate feedback message ─────────────────────────────────────── */}
      {generateMsg && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 text-xs font-medium animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {generateMsg}
        </div>
      )}

      {/* ── Error banner ─────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-xs font-medium">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ── Summary stat cards ───────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          title="Active"
          value={counts.active}
          icon={<Sparkles className="h-4 w-4" />}
          color="text-amber-500"
        />
        <StatCard
          title="Completed"
          value={counts.acted}
          icon={<CheckCircle2 className="h-4 w-4" />}
          color="text-green-500"
        />
        <StatCard
          title="Dismissed"
          value={counts.dismissed}
          icon={<XCircle className="h-4 w-4" />}
          color="text-slate-500"
        />
      </div>

      {/* ── Filters row ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Category pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide py-1">
          {categories.map((c) => (
            <button
              key={c.value}
              onClick={() => setCategoryFilter(c.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                categoryFilter === c.value
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-primary/40'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* Status toggle */}
          <div className="flex rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 text-xs font-semibold shrink-0">
            {(['active', 'all'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 transition-colors capitalize ${
                  statusFilter === s
                    ? 'bg-primary text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {s === 'all' ? 'All history' : 'Active'}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="w-52">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search…"
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
        </div>
      </div>

      {/* ── Recommendations list ─────────────────────────────────────────── */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-10 w-10" />
        </div>
      ) : filteredRecs.length === 0 ? (
        <EmptyState
          title="No recommendations found"
          description={
            counts.active === 0
              ? "Your LPG usage looks great! Click 'Refresh Insights' to run the engine anytime."
              : "No recommendations match your current filters."
          }
          icon={<Sparkles className="h-8 w-8 text-amber-400" />}
        />
      ) : (
        <div className="space-y-3">
          {filteredRecs.map((r) => {
            const isExpanded  = expandedId === r.id
            const CategoryIcon = CATEGORY_ICONS[r.category] ?? Info
            const priorityClr = PRIORITY_COLORS[r.priority] ?? PRIORITY_COLORS[3]
            const priorityLbl = PRIORITY_LABEL[r.priority] ?? 'Medium'

            return (
              <Card
                key={r.id}
                className={`transition-all hover:border-slate-200 dark:hover:border-slate-600 ${
                  r.status === 'dismissed' ? 'opacity-50' : ''
                }`}
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">

                  {/* Left — icon + content */}
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    {/* Category icon */}
                    <div className="h-9 w-9 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                      <CategoryIcon className="h-4 w-4 text-slate-600 dark:text-slate-300" />
                    </div>

                    <div className="space-y-1.5 flex-1 min-w-0">
                      {/* Badges row */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {categoryBadge(r.category as RecommendationCategory)}

                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${priorityClr}`}>
                          {priorityLbl}
                        </span>

                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">
                          {Math.round(r.confidence * 100)}% confidence
                        </span>

                        {r.status === 'acted' && (
                          <span className="text-[10px] font-bold text-green-600 dark:text-green-400 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" /> Completed
                          </span>
                        )}
                        {r.status === 'dismissed' && (
                          <span className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                            <XCircle className="h-3 w-3" /> Dismissed
                          </span>
                        )}
                      </div>

                      {/* Message */}
                      <p className="text-sm font-semibold text-slate-900 dark:text-white leading-relaxed">
                        {r.message}
                      </p>

                      {/* Timestamp */}
                      {r.created_at && (
                        <p className="text-[10px] text-slate-400">
                          Generated {new Date(r.created_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right — action buttons */}
                  <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
                    {/* Why am I seeing this? */}
                    {r.supporting_facts_json && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setExpandedId(isExpanded ? null : r.id)}
                        leftIcon={<HelpCircle className="h-3.5 w-3.5 text-primary" />}
                        className="text-xs hidden sm:flex"
                      >
                        Why?{' '}
                        {isExpanded
                          ? <ChevronUp className="h-3 w-3 ml-1" />
                          : <ChevronDown className="h-3 w-3 ml-1" />}
                      </Button>
                    )}

                    {/* Accept / Dismiss — only for active recs */}
                    {r.status === 'active' && (
                      <>
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleAct(r.id)}
                          leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                        >
                          Done
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDismiss(r.id)}
                          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                          title="Dismiss"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                {/* Supporting facts drawer */}
                {isExpanded && r.supporting_facts_json && (
                  <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-700/30 p-4 rounded-xl text-xs space-y-2 animate-in fade-in">
                    <h5 className="font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
                      <HelpCircle className="h-4 w-4 text-primary" />
                      Why am I seeing this? — Data Evidence
                    </h5>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                      {Object.entries(r.supporting_facts_json).map(([key, val]) => (
                        <div
                          key={key}
                          className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                        >
                          <span className="text-[10px] text-slate-400 block uppercase font-bold tracking-wide">
                            {key.replace(/_/g, ' ')}
                          </span>
                          <span className="font-bold text-slate-800 dark:text-slate-100 break-words">
                            {Array.isArray(val) ? val.join(', ') : String(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
