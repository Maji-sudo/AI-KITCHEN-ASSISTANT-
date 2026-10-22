import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, Sun, Moon, Bell, ShieldCheck, LogOut, User as UserIcon } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { Avatar } from '../ui/Avatar'
import { Breadcrumbs } from './Breadcrumbs'
import { useNotifications } from '@/hooks/useNotifications'

interface NavbarProps {
  onOpenMobileSidebar: () => void
}

export function Navbar({ onOpenMobileSidebar }: NavbarProps) {
  const { isDark, toggle } = useTheme()
  const { user, logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifMenu, setShowNotifMenu] = useState(false)

  const { notifications, unreadCount } = useNotifications()

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 shrink-0">
      {/* Left: Mobile Menu Button & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:block">
          <Breadcrumbs />
        </div>
      </div>

      {/* Right Action Icons */}
      <div className="flex items-center gap-2">
        {/* Safety Indicator Badge */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800 text-xs font-semibold text-green-700 dark:text-green-400">
          <ShieldCheck className="h-4 w-4" />
          <span>System Normal</span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggle}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Toggle Theme"
        >
          {isDark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifMenu(!showNotifMenu)
              setShowUserMenu(false)
            }}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors relative"
            title="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-danger ring-2 ring-white dark:ring-slate-900" />
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifMenu && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-white dark:bg-slate-800 shadow-2xl border border-slate-100 dark:border-slate-700 p-4 z-50 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-2 mb-3">
                <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">Notifications</h4>
                <Link
                  to="/notifications"
                  onClick={() => setShowNotifMenu(false)}
                  className="text-xs text-primary font-semibold hover:underline"
                >
                  View all
                </Link>
              </div>

              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1 scrollbar-hide">
                {notifications.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-400">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.slice(0, 4).map((n) => (
                    <div
                      key={n.id}
                      className={`p-2.5 rounded-xl transition-colors text-xs ${
                        !n.read
                          ? 'bg-primary/5 dark:bg-primary/10 border-l-2 border-primary'
                          : 'bg-slate-50 dark:bg-slate-700/40 hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                    >
                      <p className="font-semibold text-slate-800 dark:text-slate-100">{n.payload?.title || 'Notification'}</p>
                      <p className="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px] line-clamp-2">
                        {n.payload?.body || n.payload?.description || n.payload?.message || ''}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative ml-1">
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu)
              setShowNotifMenu(false)
            }}
            className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Avatar name={user?.name || 'Arjun Kumar'} size="sm" status="online" />
            <span className="hidden md:block text-xs font-bold text-slate-800 dark:text-slate-200">
              {user?.name || 'Arjun Kumar'}
            </span>
          </button>

          {/* User Menu Dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 rounded-2xl bg-white dark:bg-slate-800 shadow-2xl border border-slate-100 dark:border-slate-700 py-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-700">
                <p className="text-xs font-bold text-slate-800 dark:text-slate-100">{user?.name || 'Arjun Kumar'}</p>
                <p className="text-[10px] text-slate-400">{user?.phone || '+919876543210'}</p>
              </div>

              <Link
                to="/settings"
                onClick={() => setShowUserMenu(false)}
                className="flex items-center gap-2 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50"
              >
                <UserIcon className="h-4 w-4 text-slate-400" />
                Profile Settings
              </Link>

              <button
                onClick={() => {
                  setShowUserMenu(false)
                  logout()
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-xs text-danger hover:bg-red-50 dark:hover:bg-red-950/30 font-medium"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
