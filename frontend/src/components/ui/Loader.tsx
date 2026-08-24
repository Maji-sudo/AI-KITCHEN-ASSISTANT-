import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('animate-spin text-primary h-6 w-6', className)} />
}

export function LoadingScreen({ text = 'Loading SafeGas AI...' }: { text?: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-slate-600 dark:text-slate-300">
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 shadow-xl border border-slate-100 dark:border-slate-700 flex flex-col items-center gap-3">
        <Spinner className="h-10 w-10 text-primary" />
        <p className="text-sm font-medium animate-pulse">{text}</p>
      </div>
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700/60',
        className
      )}
    />
  )
}
