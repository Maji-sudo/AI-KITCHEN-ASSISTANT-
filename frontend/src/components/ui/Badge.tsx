import { cn } from '@/utils/cn'
import type { RecommendationCategory, GasStatus, BookingStatus, DeviceStatus } from '@/types'

type Variant = 'default' | 'success' | 'danger' | 'warning' | 'info' | 'outline' | 'ghost'

const variantClasses: Record<Variant, string> = {
  default: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
  success: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  danger: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  outline: 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-300',
  ghost: 'text-slate-600 dark:text-slate-400',
}

interface BadgeProps {
  children: React.ReactNode
  variant?: Variant
  className?: string
  dot?: boolean
}

export function Badge({ children, variant = 'default', className, dot }: BadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
      variantClasses[variant], className
    )}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}

export function categoryBadge(cat: RecommendationCategory) {
  const map: Record<RecommendationCategory, { label: string; variant: Variant }> = {
    safety: { label: '🔴 Safety', variant: 'danger' },
    efficiency: { label: '💡 Efficiency', variant: 'warning' },
    cooking: { label: '🍳 Cooking', variant: 'info' },
    refill: { label: '🔋 Refill', variant: 'success' },
    general: { label: '📌 General', variant: 'default' },
  }
  const { label, variant } = map[cat]
  return <Badge variant={variant}>{label}</Badge>
}

export function gasStatusBadge(status: GasStatus) {
  const map: Record<GasStatus, { label: string; variant: Variant }> = {
    normal: { label: '✅ Safe (Normal)', variant: 'success' },
    safe: { label: '✅ Safe', variant: 'success' },
    warning: { label: '⚠️ Warning', variant: 'warning' },
    critical: { label: '🚨 Critical (Leak)', variant: 'danger' },
    danger: { label: '🚨 Danger', variant: 'danger' },
  }
  const item = map[status] || { label: String(status), variant: 'default' }
  return <Badge variant={item.variant}>{item.label}</Badge>
}

export function bookingStatusBadge(status: BookingStatus) {
  const map: Record<BookingStatus, { label: string; variant: Variant }> = {
    pending: { label: 'Pending', variant: 'warning' },
    confirmed: { label: 'Confirmed', variant: 'info' },
    delivered: { label: 'Delivered', variant: 'success' },
    cancelled: { label: 'Cancelled', variant: 'danger' },
  }
  const { label, variant } = map[status]
  return <Badge variant={variant}>{label}</Badge>
}

export function deviceStatusBadge(status: DeviceStatus) {
  const map: Record<DeviceStatus, { label: string; variant: Variant }> = {
    active: { label: 'Active', variant: 'success' },
    inactive: { label: 'Inactive', variant: 'default' },
    offline: { label: 'Offline', variant: 'danger' },
    error: { label: 'Error', variant: 'danger' },
  }
  const { label, variant } = map[status]
  return <Badge variant={variant} dot>{label}</Badge>
}
