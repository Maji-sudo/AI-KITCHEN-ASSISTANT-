import { cn } from '@/utils/cn'
import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  onClick?: () => void
}

export function Card({ children, className, hover, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 p-5 card-shadow',
        hover && 'hover:shadow-md transition-shadow cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('flex items-center justify-between mb-4', className)}>{children}</div>
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn('text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide', className)}>{children}</h3>
}

export function CardValue({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn('text-2xl font-bold text-slate-900 dark:text-white', className)}>{children}</p>
}

export function StatCard({
  title, value, subtitle, icon, color = 'text-primary', trend,
}: {
  title: string; value: React.ReactNode; subtitle?: string
  icon: React.ReactNode; color?: string; trend?: { value: number; label: string }
}) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">{title}</p>
          <p className={cn('mt-1 text-2xl font-bold', color)}>{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
          {trend && (
            <p className={cn('mt-1 text-xs font-medium', trend.value >= 0 ? 'text-green-500' : 'text-red-500')}>
              {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
            </p>
          )}
        </div>
        <div className={cn('p-2.5 rounded-lg bg-slate-50 dark:bg-slate-700/50', color)}>{icon}</div>
      </div>
    </Card>
  )
}
