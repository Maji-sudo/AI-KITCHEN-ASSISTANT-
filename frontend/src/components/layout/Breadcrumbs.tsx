import { useLocation, Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  safety: 'Safety & Leak Monitoring',
  analytics: 'Consumption Analytics',
  cylinder: 'Cylinder & Refills',
  cooking: 'AI Cooking Assistant',
  recommendations: 'AI Recommendations',
  efficiency: 'Efficiency Score',
  devices: 'Paired Devices',
  notifications: 'Notification Center',
  settings: 'Settings & Account',
}

export function Breadcrumbs() {
  const location = useLocation()
  const pathnames = location.pathname.split('/').filter(Boolean)

  return (
    <nav className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
      <Link to="/" className="hover:text-primary transition-colors flex items-center gap-1 font-medium">
        <Home className="h-3.5 w-3.5" />
        <span>Home</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`
        const isLast = index === pathnames.length - 1
        const label = routeLabels[value] || value

        return (
          <div key={to} className="flex items-center gap-1.5">
            <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
            {isLast ? (
              <span className="font-semibold text-slate-800 dark:text-slate-200">{label}</span>
            ) : (
              <Link to={to} className="hover:text-primary transition-colors font-medium">
                {label}
              </Link>
            )}
          </div>
        )
      })}
    </nav>
  )
}
