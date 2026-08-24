import { cn } from '@/utils/cn'

interface GaugeProps {
  value: number // 0 to 100
  size?: number
  strokeWidth?: number
  label?: string
  sublabel?: string
  color?: string
  className?: string
}

export function Gauge({
  value,
  size = 140,
  strokeWidth = 12,
  label,
  sublabel,
  color = '#16a34a',
  className,
}: GaugeProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clampedValue = Math.min(100, Math.max(0, value))
  const strokeDashoffset = circumference - (clampedValue / 100) * circumference

  return (
    <div className={cn('flex flex-col items-center justify-center relative', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-100 dark:text-slate-700 fill-none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="fill-none transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-extrabold text-slate-900 dark:text-white">
          {label ?? `${clampedValue}%`}
        </span>
        {sublabel && (
          <span className="text-xs font-medium text-slate-400 dark:text-slate-500 mt-0.5">
            {sublabel}
          </span>
        )}
      </div>
    </div>
  )
}
