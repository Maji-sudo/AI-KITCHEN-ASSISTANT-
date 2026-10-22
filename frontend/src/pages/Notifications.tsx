import { useState } from 'react'
import {
  Bell,
  CheckCheck,
  Search,
  ShieldAlert,
  Flame,
  Zap,
  ChefHat,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Info,
  WifiOff,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useNotifications } from '@/hooks/useNotifications'
import type { Notification, NotificationSeverity } from '@/types'
import { formatDateTime } from '@/utils/cn'

type FilterTab = 'all' | 'unread' | 'safety' | 'reminder'

export function Notifications() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Pass active filter to backend query
  const {
    notifications,
    unreadCount,
    isLoading,
    isError,
    refetch,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearNotifications,
    isMarkingAllRead,
  } = useNotifications(activeTab === 'unread' ? undefined : activeTab, activeTab === 'unread')

  const filteredNotifs = notifications.filter((n) => {
    const title = (n.payload?.title || '').toLowerCase()
    const body = (n.payload?.body || n.payload?.description || n.payload?.message || '').toLowerCase()
    const q = searchQuery.toLowerCase().trim()
    if (!q) return true
    return title.includes(q) || body.includes(q)
  })

  const getSeverityBadge = (severity?: NotificationSeverity, channel?: string) => {
    const sev = severity || (channel === 'emergency' ? 'critical' : channel === 'safety' ? 'warning' : 'info')
    switch (sev) {
      case 'critical':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-red-100 text-red-700 dark:bg-red-950/70 dark:text-red-300 border border-red-200 dark:border-red-900 animate-pulse">
            🚨 Critical
          </span>
        )
      case 'warning':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 dark:bg-amber-950/70 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
            ⚠️ Warning
          </span>
        )
      case 'reminder':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
            🔔 Reminder
          </span>
        )
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-700 dark:bg-slate-700/60 dark:text-slate-300">
            ℹ️ Info
          </span>
        )
    }
  }

  const getCategoryIcon = (category?: string, severity?: string) => {
    if (severity === 'critical') {
      return <ShieldAlert className="h-5 w-5 text-danger" />
    }
    switch (category) {
      case 'safety':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />
      case 'refill':
        return <Flame className="h-5 w-5 text-primary" />
      case 'efficiency':
        return <Zap className="h-5 w-5 text-yellow-500" />
      case 'cooking':
        return <ChefHat className="h-5 w-5 text-blue-500" />
      case 'device':
        return <WifiOff className="h-5 w-5 text-slate-500" />
      default:
        return <Info className="h-5 w-5 text-slate-400" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <Bell className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Notification Center</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-danger text-white">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Real-time safety alarms, gas leak detections, cylinder refill reminders, and device health status.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            title="Refresh alerts"
          >
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllAsRead()}
            isLoading={isMarkingAllRead}
            disabled={unreadCount === 0}
            leftIcon={<CheckCheck className="h-4 w-4" />}
          >
            Mark All Read
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => clearNotifications(false)}
            className="text-xs text-slate-500 hover:text-danger hover:bg-red-50 dark:hover:bg-red-950/30"
            title="Clear read alerts"
            leftIcon={<Trash2 className="h-3.5 w-3.5" />}
          >
            Clear Read
          </Button>
        </div>
      </div>

      {/* Filter Tabs & Search Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
          {[
            { id: 'all' as FilterTab, label: 'All Alerts' },
            { id: 'unread' as FilterTab, label: `Unread (${unreadCount})` },
            { id: 'safety' as FilterTab, label: 'Safety Alerts' },
            { id: 'reminder' as FilterTab, label: 'Refill Reminders' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
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

      {/* Notification List State */}
      <div className="space-y-3">
        {isLoading ? (
          <Card className="text-center py-16 space-y-3">
            <RefreshCw className="h-8 w-8 text-primary animate-spin mx-auto opacity-75" />
            <p className="text-xs text-slate-500 font-medium">Loading notifications from server...</p>
          </Card>
        ) : isError ? (
          <Card className="text-center py-12 space-y-3 border-red-200 dark:border-red-900 bg-red-50/20 dark:bg-red-950/10">
            <ShieldAlert className="h-8 w-8 text-danger mx-auto" />
            <p className="text-xs font-bold text-danger">Failed to load notifications.</p>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              Try Again
            </Button>
          </Card>
        ) : filteredNotifs.length === 0 ? (
          <Card className="text-center py-16 space-y-3 text-slate-400">
            <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
              <Bell className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-700 dark:text-slate-300">No notifications found</p>
              <p className="text-xs text-slate-400 mt-1">
                {activeTab === 'unread'
                  ? 'You are all caught up! No unread notifications.'
                  : activeTab === 'safety'
                  ? 'No safety alerts recorded. All systems operating safely.'
                  : activeTab === 'reminder'
                  ? 'No refill reminders. Your cylinder gas levels are healthy.'
                  : searchQuery
                  ? `No alerts matching "${searchQuery}".`
                  : 'You will receive notifications here for gas alerts and refill reminders.'}
              </p>
            </div>
          </Card>
        ) : (
          filteredNotifs.map((n: Notification) => {
            const isUnread = !n.read
            const payload = n.payload || {}
            const title = payload.title || 'SafeGas Alert'
            const body = payload.body || payload.description || payload.message || ''
            const severity = payload.severity as NotificationSeverity | undefined
            const isCritical = severity === 'critical' || n.channel === 'emergency'

            return (
              <Card
                key={n.id}
                className={`transition-all ${
                  isCritical
                    ? 'border-l-4 border-l-danger bg-red-50/20 dark:bg-red-950/20 border-red-200 dark:border-red-900/60 shadow-xs'
                    : isUnread
                    ? 'border-l-4 border-l-primary bg-primary/5 dark:bg-primary/10'
                    : ''
                }`}
              >
                <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                  <div className="flex items-start gap-3 w-full">
                    <div
                      className={`p-2.5 rounded-xl shrink-0 ${
                        isCritical
                          ? 'bg-red-100 dark:bg-red-950/60 text-danger'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {getCategoryIcon(payload.category, severity)}
                    </div>

                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-snug">
                          {title}
                        </h4>
                        {getSeverityBadge(severity, n.channel)}
                        <span className="text-[10px] font-semibold text-slate-400 uppercase">
                          Via {n.channel}
                        </span>
                        {payload.device_id && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-slate-500 dark:text-slate-400">
                            {payload.device_id}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                        {body}
                      </p>

                      <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400">
                        <span>{formatDateTime(n.sent_at)}</span>
                        {n.delivery_status && (
                          <span className="capitalize">• Status: {n.delivery_status}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    {isUnread && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => markAsRead(n.id)}
                        className="text-xs text-primary font-bold hover:bg-primary/10"
                      >
                        Mark Read
                      </Button>
                    )}

                    <button
                      onClick={() => deleteNotification(n.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-danger hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                      title="Delete notification"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
