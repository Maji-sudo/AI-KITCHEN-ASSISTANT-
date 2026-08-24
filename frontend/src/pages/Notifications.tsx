import { useState } from 'react'
import {
  Bell,
  CheckCheck,
  Search,
  ShieldAlert,
  Flame,
  Zap,
  ChefHat,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { mockNotifications } from '@/utils/mockData'
import type { Notification } from '@/types'
import { formatDateTime } from '@/utils/cn'

export function Notifications() {
  const [notifs, setNotifs] = useState<Notification[]>(mockNotifications)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const handleMarkRead = (id: number) => {
    setNotifs((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }

  const handleMarkAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  const filteredNotifs = notifs.filter((n) => {
    const matchesFilter = filter === 'all' || !n.read
    const matchesQuery =
      n.payload.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.payload.body.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesQuery
  })

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'safety':
        return <ShieldAlert className="h-5 w-5 text-danger" />
      case 'refill':
        return <Flame className="h-5 w-5 text-amber-500" />
      case 'efficiency':
        return <Zap className="h-5 w-5 text-primary" />
      case 'cooking':
        return <ChefHat className="h-5 w-5 text-blue-500" />
      default:
        return <Bell className="h-5 w-5 text-slate-400" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center shrink-0">
            <Bell className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Notification Center</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Review FCM push alerts, SMS notifications, and WhatsApp updates.
            </p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={handleMarkAllRead} leftIcon={<CheckCheck className="h-4 w-4" />}>
          Mark All Read
        </Button>
      </div>

      {/* Filter & Search Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors ${
              filter === 'all'
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
            }`}
          >
            All Alerts ({notifs.length})
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors ${
              filter === 'unread'
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
            }`}
          >
            Unread ({notifs.filter((n) => !n.read).length})
          </button>
        </div>

        <div className="w-full sm:w-64">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search alerts..."
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
      </div>

      {/* Notification List */}
      <div className="space-y-3">
        {filteredNotifs.length === 0 ? (
          <Card className="text-center py-12 text-slate-400 text-xs">
            No notifications found.
          </Card>
        ) : (
          filteredNotifs.map((n) => (
            <Card
              key={n.id}
              className={`transition-all ${
                !n.read ? 'border-l-4 border-l-primary bg-primary/5 dark:bg-primary/10' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-700 shrink-0">
                    {getCategoryIcon(n.payload.category)}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                        {n.payload.title}
                      </h4>
                      <span className="text-[10px] uppercase font-bold text-slate-400">
                        Via {n.channel}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
                      {n.payload.body}
                    </p>

                    <span className="text-[10px] text-slate-400 block mt-1">
                      {formatDateTime(n.sent_at)}
                    </span>
                  </div>
                </div>

                {!n.read && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleMarkRead(n.id)}
                    className="text-xs text-primary font-bold hover:underline shrink-0"
                  >
                    Mark Read
                  </Button>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
