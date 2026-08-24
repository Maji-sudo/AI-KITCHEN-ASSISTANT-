import { useState } from 'react'
import {
  Sparkles,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { categoryBadge } from '@/components/ui/Badge'
import { mockRecommendations } from '@/utils/mockData'
import type { Recommendation, RecommendationCategory } from '@/types'

export function Recommendations() {
  const [recs, setRecs] = useState<Recommendation[]>(mockRecommendations)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const categories: { label: string; value: string }[] = [
    { label: 'All Insights', value: 'all' },
    { label: '🔴 Safety', value: 'safety' },
    { label: '💡 Efficiency', value: 'efficiency' },
    { label: '🍳 Cooking', value: 'cooking' },
    { label: '🔋 Refill', value: 'refill' },
  ]

  const handleAction = (id: number, status: 'acted' | 'dismissed') => {
    setRecs((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status } : r))
    )
  }

  const filteredRecs = recs.filter((r) => {
    const matchesCat = categoryFilter === 'all' || r.category === categoryFilter
    const matchesQuery = r.message.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCat && matchesQuery
  })

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-amber-100 dark:bg-amber-950/40 text-amber-500 flex items-center justify-center shrink-0">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">AI Recommendations Engine</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Personalized LPG saving strategies & safety recommendations backed by telemetry data.
            </p>
          </div>
        </div>
      </div>

      {/* Filters & Search Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide py-1">
          {categories.map((c) => (
            <button
              key={c.value}
              onClick={() => setCategoryFilter(c.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                categoryFilter === c.value
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="w-full sm:w-64">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search recommendations..."
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecs.length === 0 ? (
          <Card className="text-center py-12 text-slate-400 text-xs">
            No recommendations match your selected filters.
          </Card>
        ) : (
          filteredRecs.map((r) => {
            const isExpanded = expandedId === r.id
            return (
              <Card key={r.id} className="transition-all hover:border-slate-200 dark:hover:border-slate-600">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {categoryBadge(r.category as RecommendationCategory)}
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {Math.round(r.confidence * 100)}% Confidence
                      </span>
                      {r.status === 'acted' && (
                        <span className="text-[10px] font-bold text-green-600 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Completed
                        </span>
                      )}
                    </div>

                    <p className="text-sm font-semibold text-slate-900 dark:text-white leading-relaxed">
                      {r.message}
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setExpandedId(isExpanded ? null : r.id)}
                      leftIcon={<HelpCircle className="h-3.5 w-3.5 text-primary" />}
                      className="text-xs"
                    >
                      Why am I seeing this? {isExpanded ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
                    </Button>

                    {r.status === 'active' && (
                      <>
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleAction(r.id, 'acted')}
                          leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                        >
                          Accept
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleAction(r.id, 'dismissed')}
                          className="text-slate-400 hover:text-slate-600"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                {/* Supporting Facts JSON Drawer ("Why am I seeing this?") */}
                {isExpanded && r.supporting_facts_json && (
                  <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-700/30 p-4 rounded-xl text-xs space-y-2 animate-in fade-in">
                    <h5 className="font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
                      <HelpCircle className="h-4 w-4 text-primary" />
                      Supporting Facts & Data Proof (Explainability Layer)
                    </h5>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                      {Object.entries(r.supporting_facts_json).map(([key, val]) => (
                        <div key={key} className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                          <span className="text-[10px] text-slate-400 block uppercase font-bold">{key.replace('_', ' ')}</span>
                          <span className="font-bold text-slate-800 dark:text-slate-100">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
