import { cn } from '@/utils/cn'

interface AvatarProps {
  name?: string
  src?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  status?: 'online' | 'offline' | 'busy'
}

export function Avatar({ name = '', src, size = 'md', className, status }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase()

  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
  }

  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-slate-400',
    busy: 'bg-red-500',
  }

  return (
    <div className="relative inline-block">
      <div
        className={cn(
          'flex items-center justify-center rounded-full bg-primary/10 text-primary font-semibold overflow-hidden border border-primary/20',
          sizes[size],
          className
        )}
      >
        {src ? (
          <img src={src} alt={name} className="h-full w-full object-cover" />
        ) : (
          <span>{initials || 'U'}</span>
        )}
      </div>
      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full ring-2 ring-white dark:ring-slate-800',
            statusColors[status]
          )}
        />
      )}
    </div>
  )
}
