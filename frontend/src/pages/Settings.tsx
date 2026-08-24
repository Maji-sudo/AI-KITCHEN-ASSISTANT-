import { useState } from 'react'
import {
  User,
  Globe,
  Bell,
  Moon,
  Sun,
  LogOut,
  Save,
  CheckCircle2,
  Shield,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'

export function Settings() {
  const { user, logout } = useAuth()
  const { isDark, toggle } = useTheme()

  const [name, setName] = useState(user?.name || 'Arjun Kumar')
  const [email, setEmail] = useState(user?.email || 'arjun@example.com')
  const [language, setLanguage] = useState(user?.language_pref || 'en')

  // Notification Preferences
  const [fcmEnabled, setFcmEnabled] = useState(true)
  const [smsEnabled, setSmsEnabled] = useState(true)
  const [whatsappEnabled, setWhatsappEnabled] = useState(true)

  const [isSaved, setIsSaved] = useState(false)

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Banner */}
      <div className="flex items-center justify-between p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center shrink-0">
            <User className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Account & System Settings</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Manage profile info, language preferences, notification gateways, and theme settings.
            </p>
          </div>
        </div>
      </div>

      {/* Profile Info Card */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <User className="h-4 w-4 text-primary" />
            User Profile Information
          </h3>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Input
              label="Phone Number (Read-only)"
              value={user?.phone || '+919876543210'}
              disabled
              className="bg-slate-100 dark:bg-slate-700/50 cursor-not-allowed opacity-75"
            />
          </div>

          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <div className="flex items-center justify-between pt-2">
            {isSaved ? (
              <span className="text-xs text-green-600 font-bold flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" /> Profile Updated Successfully!
              </span>
            ) : (
              <span />
            )}
            <Button type="submit" size="sm" leftIcon={<Save className="h-4 w-4" />}>
              Save Profile
            </Button>
          </div>
        </form>
      </Card>

      {/* Language & Regional Settings */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Globe className="h-4 w-4 text-blue-500" />
            Language & Region Preference
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { id: 'en', label: 'English', sub: 'Default' },
            { id: 'hi', label: 'हिंदी (Hindi)', sub: 'North India' },
            { id: 'ta', label: 'தமிழ் (Tamil)', sub: 'South India' },
          ].map((lang) => (
            <button
              key={lang.id}
              onClick={() => setLanguage(lang.id as 'en' | 'hi' | 'ta')}
              className={`p-3.5 rounded-xl border text-left text-xs transition-colors ${
                language === lang.id
                  ? 'border-primary bg-primary/10 text-slate-900 dark:text-white font-bold'
                  : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30 text-slate-600 dark:text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span>{lang.label}</span>
                {language === lang.id && <CheckCircle2 className="h-4 w-4 text-primary" />}
              </div>
              <span className="text-[10px] text-slate-400 font-normal mt-0.5 block">{lang.sub}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Notification Channel Preferences */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Bell className="h-4 w-4 text-amber-500" />
            Notification Gateways & Channels
          </h3>
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">FCM Push Notifications</p>
              <p className="text-[11px] text-slate-400">Real-time mobile & browser alerts for gas leaks</p>
            </div>
            <input
              type="checkbox"
              checked={fcmEnabled}
              onChange={(e) => setFcmEnabled(e.target.checked)}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">SMS Gateway Alerts</p>
              <p className="text-[11px] text-slate-400">High-priority SMS alerts when leak &gt; 1000 PPM</p>
            </div>
            <input
              type="checkbox"
              checked={smsEnabled}
              onChange={(e) => setSmsEnabled(e.target.checked)}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">WhatsApp Business API</p>
              <p className="text-[11px] text-slate-400">Weekly efficiency score reports & refill reminders</p>
            </div>
            <input
              type="checkbox"
              checked={whatsappEnabled}
              onChange={(e) => setWhatsappEnabled(e.target.checked)}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>
        </div>
      </Card>

      {/* Dark Mode & Appearance */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              {isDark ? <Moon className="h-4 w-4 text-amber-400" /> : <Sun className="h-4 w-4 text-amber-500" />}
              Appearance Mode
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Switch between Light Mode and Dark Mode for low-light kitchen monitoring.
            </p>
          </div>

          <Button variant="outline" size="sm" onClick={toggle}>
            {isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          </Button>
        </div>
      </Card>

      {/* Logout Action */}
      <Card className="border-red-100 dark:border-red-950/40 bg-red-50/30 dark:bg-red-950/10">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-danger flex items-center gap-2">
              <Shield className="h-4 w-4" /> Sign Out of Account
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              You will need to verify your phone number via OTP to sign back in.
            </p>
          </div>

          <Button variant="danger" size="sm" onClick={logout} leftIcon={<LogOut className="h-4 w-4" />}>
            Sign Out
          </Button>
        </div>
      </Card>
    </div>
  )
}
