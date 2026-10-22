import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ShieldAlert,
  BarChart3,
  Flame,
  ChefHat,
  Sparkles,
  Zap,
  Cpu,
  Bell,
  Settings,
  X,
  Radio,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { useNotifications } from '@/hooks/useNotifications'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { unreadCount } = useNotifications()

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Safety', path: '/safety', icon: ShieldAlert, badge: 'Live', badgeColor: 'bg-red-500' },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Cylinder', path: '/cylinder', icon: Flame },
    { name: 'Cooking Assistant', path: '/cooking', icon: ChefHat, badge: 'AI', badgeColor: 'bg-primary' },
    { name: 'Recommendations', path: '/recommendations', icon: Sparkles },
    { name: 'Efficiency', path: '/efficiency', icon: Zap },
    { name: 'Devices', path: '/devices', icon: Cpu },
    {
      name: 'Notifications',
      path: '/notifications',
      icon: Bell,
      badge: unreadCount > 0 ? `${unreadCount}` : undefined,
      badgeColor: 'bg-danger',
    },
    { name: 'Settings', path: '/settings', icon: Settings },
  ]
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Drawer */}
      <aside
        className={cn(
          'fixed top-0 bottom-0 left-0 z-50 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:h-full shrink-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-md shadow-primary/30">
              <Flame className="h-5 w-5 fill-current" />
            </div>
            <div>
              <h1 className="text-base font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-1">
                SafeGas <span className="text-primary">AI</span>
              </h1>
              <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Smart LPG Ecosystem</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="md:hidden text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Status Chip */}
        <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
              <Radio className="h-3.5 w-3.5 text-primary animate-pulse" />
              SGD-001-ESP32
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-100 text-green-700 dark:bg-green-950/60 dark:text-green-400">
              Online
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 scrollbar-hide">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150',
                    isActive
                      ? 'bg-primary text-white shadow-md shadow-primary/25 font-bold'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-slate-200'
                  )
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded-full text-[9px] font-extrabold text-white uppercase tracking-wider',
                      item.badgeColor
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 text-center">
          SafeGas AI v1.0.0 &bull; 2026
        </div>
      </aside>
    </>
  )
}
