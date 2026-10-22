import { useState, useEffect } from 'react'
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
  MapPin,
  Trash2,
  Edit3,
  Cpu,
  AlertCircle,
  Loader2,
  Radio,
  Wifi,
  Battery,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { settingsService } from '@/services/settings.service'
import type { DeliveryAddress, NotificationPreferences, SafetyPreferences, DeviceSummary } from '@/types'

export function Settings() {
  const { user, logout } = useAuth()
  const { isDark, toggle } = useTheme()

  // Loading & Global Status
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  // Profile State
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [language, setLanguage] = useState('en')
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [profileSuccessMsg, setProfileSuccessMsg] = useState('')
  const [profileErrorMsg, setProfileErrorMsg] = useState('')

  // Target Delivery Address State
  const [savedAddress, setSavedAddress] = useState<DeliveryAddress | null>(null)
  const [isEditingAddress, setIsEditingAddress] = useState(false)
  const [addressLine, setAddressLine] = useState('')
  const [area, setArea] = useState('')
  const [city, setCity] = useState('')
  const [stateName, setStateName] = useState('')
  const [pincode, setPincode] = useState('')
  const [isSavingAddress, setIsSavingAddress] = useState(false)
  const [isClearingAddress, setIsClearingAddress] = useState(false)
  const [addressSuccessMsg, setAddressSuccessMsg] = useState('')
  const [addressErrorMsg, setAddressErrorMsg] = useState('')

  // Notification Preferences State
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences>({
    fcm_enabled: true,
    sms_enabled: true,
    whatsapp_enabled: true,
    gas_leak_alerts: true,
    cylinder_refill_reminders: true,
    weekly_efficiency_reports: true,
    device_offline_alerts: true,
  })
  const [isSavingNotifs, setIsSavingNotifs] = useState(false)
  const [notifSuccessMsg, setNotifSuccessMsg] = useState('')

  // Safety Preferences State
  const [safetyPrefs, setSafetyPrefs] = useState<SafetyPreferences>({
    emergency_buzzer: true,
    auto_shutoff_enabled: true,
    leak_sensitivity: 'high',
    warning_threshold_ppm: 500,
  })
  const [isSavingSafety, setIsSavingSafety] = useState(false)
  const [safetySuccessMsg, setSafetySuccessMsg] = useState('')

  // Connected Devices State
  const [devices, setDevices] = useState<DeviceSummary[]>([])

  // Load real settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setIsLoading(true)
    setLoadError('')
    try {
      const data = await settingsService.getSettings()
      // Profile
      setName(data.profile.name || user?.name || '')
      setEmail(data.profile.email || user?.email || '')
      setPhone(data.profile.phone || user?.phone || '')
      setLanguage(data.profile.language_pref || 'en')

      // Delivery Address
      if (data.delivery_address) {
        setSavedAddress(data.delivery_address)
        setAddressLine(data.delivery_address.address_line || '')
        setArea(data.delivery_address.area || '')
        setCity(data.delivery_address.city || '')
        setStateName(data.delivery_address.state || '')
        setPincode(data.delivery_address.pincode || '')
        setIsEditingAddress(false)
      } else {
        setSavedAddress(null)
        setAddressLine('')
        setArea('')
        setCity('')
        setStateName('')
        setPincode('')
        setIsEditingAddress(true)
      }

      // Preferences
      if (data.notification_preferences) {
        setNotifPrefs(data.notification_preferences)
      }
      if (data.safety_preferences) {
        setSafetyPrefs(data.safety_preferences)
      }

      // Devices
      setDevices(data.devices || [])
    } catch (err: any) {
      setLoadError('Failed to load settings from server. Please verify backend connection.')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle Save Profile
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSavingProfile(true)
    setProfileSuccessMsg('')
    setProfileErrorMsg('')

    if (!name.trim()) {
      setProfileErrorMsg('Full name cannot be blank.')
      setIsSavingProfile(false)
      return
    }

    try {
      await settingsService.updateProfile({
        name: name.trim(),
        phone: phone.trim() || undefined,
        language_pref: language,
      })
      setProfileSuccessMsg('Profile updated successfully!')
      setTimeout(() => setProfileSuccessMsg(''), 4000)
    } catch (err: any) {
      setProfileErrorMsg(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setIsSavingProfile(false)
    }
  }

  // Handle Save Target Delivery Address
  const handleSaveAddress = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSavingAddress(true)
    setAddressSuccessMsg('')
    setAddressErrorMsg('')

    if (!addressLine.trim() || !area.trim() || !city.trim() || !stateName.trim() || !pincode.trim()) {
      setAddressErrorMsg('All address fields (Address Line, Area, City, State, PIN Code) are required.')
      setIsSavingAddress(false)
      return
    }

    try {
      const res = await settingsService.saveAddress({
        address_line: addressLine.trim(),
        area: area.trim(),
        city: city.trim(),
        state: stateName.trim(),
        pincode: pincode.trim(),
      })
      setSavedAddress(res.delivery_address)
      setIsEditingAddress(false)
      setAddressSuccessMsg('Delivery address saved successfully!')
      setTimeout(() => setAddressSuccessMsg(''), 4000)
    } catch (err: any) {
      setAddressErrorMsg(err.response?.data?.detail || 'Failed to save delivery address.')
    } finally {
      setIsSavingAddress(false)
    }
  }

  // Handle Clear Target Delivery Address
  const handleClearAddress = async () => {
    if (!window.confirm('Are you sure you want to remove your saved target delivery address?')) {
      return
    }
    setIsClearingAddress(true)
    setAddressSuccessMsg('')
    setAddressErrorMsg('')

    try {
      await settingsService.clearAddress()
      setSavedAddress(null)
      setAddressLine('')
      setArea('')
      setCity('')
      setStateName('')
      setPincode('')
      setIsEditingAddress(true)
      setAddressSuccessMsg('Delivery address cleared successfully.')
      setTimeout(() => setAddressSuccessMsg(''), 4000)
    } catch (err: any) {
      setAddressErrorMsg(err.response?.data?.detail || 'Failed to clear delivery address.')
    } finally {
      setIsClearingAddress(false)
    }
  }

  // Handle Save Notification Preferences
  const handleSaveNotificationPrefs = async () => {
    setIsSavingNotifs(true)
    setNotifSuccessMsg('')
    try {
      await settingsService.updateNotificationPreferences(notifPrefs)
      setNotifSuccessMsg('Notification preferences updated!')
      setTimeout(() => setNotifSuccessMsg(''), 4000)
    } catch {
      // keep state
    } finally {
      setIsSavingNotifs(false)
    }
  }

  // Handle Save Safety Preferences
  const handleSaveSafetyPrefs = async () => {
    setIsSavingSafety(true)
    setSafetySuccessMsg('')
    try {
      await settingsService.updateSafetyPreferences(safetyPrefs)
      setSafetySuccessMsg('Safety preferences updated!')
      setTimeout(() => setSafetySuccessMsg(''), 4000)
    } catch {
      // keep state
    } finally {
      setIsSavingSafety(false)
    }
  }

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
        <p className="text-xs text-slate-500 font-semibold">Loading settings and configurations...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="flex items-center justify-between p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <User className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Account & System Settings</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Manage profile info, cylinder refill delivery address, notification gateways, and safety parameters.
            </p>
          </div>
        </div>
      </div>

      {loadError && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-xs text-danger flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{loadError}</span>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 1. Target Address for Cylinder Refill Booking (MANDATORY REQUIREMENT) */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card className="border-2 border-primary/20 dark:border-primary/30">
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4 flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <MapPin className="h-4 w-4 text-primary" />
              Target Address for Cylinder Refill
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              This address is used exclusively as your target delivery destination for LPG refill bookings.
            </p>
          </div>

          {savedAddress && !isEditingAddress && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsEditingAddress(true)}
                leftIcon={<Edit3 className="h-3.5 w-3.5" />}
              >
                Edit Address
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleClearAddress}
                isLoading={isClearingAddress}
                leftIcon={<Trash2 className="h-3.5 w-3.5 text-danger" />}
                className="text-danger hover:bg-red-50 dark:hover:bg-red-950/30"
              >
                Clear Address
              </Button>
            </div>
          )}
        </div>

        {addressSuccessMsg && (
          <div className="mb-4 p-3 rounded-xl bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-900 text-xs text-green-700 dark:text-green-300 flex items-center gap-2 animate-fadeIn">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
            <span>{addressSuccessMsg}</span>
          </div>
        )}

        {addressErrorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-danger flex items-center gap-2 animate-fadeIn">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{addressErrorMsg}</span>
          </div>
        )}

        {/* Display Saved Address Card */}
        {savedAddress && !isEditingAddress ? (
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-700/30 border border-slate-200 dark:border-slate-700 space-y-2">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-bold text-xs text-slate-900 dark:text-white">
                  {savedAddress.address_line}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  {savedAddress.area}, {savedAddress.city}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  {savedAddress.state} — <span className="font-mono font-semibold">{savedAddress.pincode}</span>
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-800 dark:bg-green-950/60 dark:text-green-300">
                ✓ Saved in Database
              </span>
            </div>
            <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-200 dark:border-slate-700/60">
              💡 This address will be used automatically when opening the Cylinder Refill booking modal.
            </p>
          </div>
        ) : (
          /* Address Entry / Edit Form */
          <form onSubmit={handleSaveAddress} className="space-y-4">
            <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 text-xs text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900/50">
              📌 <strong>Manual Address Entry:</strong> Please enter your delivery address below. SafeGas AI never auto-populates your address from GPS, browser location, or demo values without your explicit choice.
            </div>

            <Input
              label="Address Line (House / Flat No., Street, Building)"
              placeholder="e.g. Flat 302, Sunrise Orchid Apartments"
              value={addressLine}
              onChange={(e) => setAddressLine(e.target.value)}
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Area / Locality / Landmark"
                placeholder="e.g. Koramangala 4th Block"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                required
              />
              <Input
                label="City"
                placeholder="e.g. Bengaluru"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="State"
                placeholder="e.g. Karnataka"
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                required
              />
              <Input
                label="PIN Code (Postal Code)"
                placeholder="e.g. 560034"
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                required
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              {savedAddress && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditingAddress(false)}
                >
                  Cancel Edit
                </Button>
              )}
              <div className="ml-auto flex items-center gap-2">
                <Button
                  type="submit"
                  size="sm"
                  isLoading={isSavingAddress}
                  leftIcon={<Save className="h-4 w-4" />}
                >
                  Save Delivery Address
                </Button>
              </div>
            </div>
          </form>
        )}
      </Card>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 2. User Profile Info Card                                          */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <User className="h-4 w-4 text-primary" />
            User Profile Information
          </h3>
        </div>

        {profileSuccessMsg && (
          <div className="mb-4 p-3 rounded-xl bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-900 text-xs text-green-700 dark:text-green-300 flex items-center gap-2 animate-fadeIn">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
            <span>{profileSuccessMsg}</span>
          </div>
        )}

        {profileErrorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-danger flex items-center gap-2 animate-fadeIn">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{profileErrorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Input
              label="Phone Number"
              placeholder="+91..."
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <Input
            label="Email Address (Account Identifier)"
            type="email"
            value={email}
            disabled
            className="bg-slate-100 dark:bg-slate-700/50 cursor-not-allowed opacity-75"
          />

          <div className="flex items-center justify-end pt-2">
            <Button type="submit" size="sm" isLoading={isSavingProfile} leftIcon={<Save className="h-4 w-4" />}>
              Save Profile
            </Button>
          </div>
        </form>
      </Card>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 3. Language & Regional Settings                                    */}
      {/* ─────────────────────────────────────────────────────────────────── */}
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
              onClick={() => {
                setLanguage(lang.id)
                settingsService.updateProfile({ language_pref: lang.id })
              }}
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

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 4. Notification Preferences Card                                   */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Bell className="h-4 w-4 text-amber-500" />
            Notification Channels & Categories
          </h3>
          {notifSuccessMsg && (
            <span className="text-xs text-green-600 font-bold flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" /> {notifSuccessMsg}
            </span>
          )}
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">FCM Push Notifications</p>
              <p className="text-[11px] text-slate-400">Real-time mobile & browser alerts for critical gas leaks</p>
            </div>
            <input
              type="checkbox"
              checked={notifPrefs.fcm_enabled}
              onChange={(e) => setNotifPrefs({ ...notifPrefs, fcm_enabled: e.target.checked })}
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
              checked={notifPrefs.sms_enabled}
              onChange={(e) => setNotifPrefs({ ...notifPrefs, sms_enabled: e.target.checked })}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">WhatsApp Notification Service</p>
              <p className="text-[11px] text-slate-400">Refill reminders and weekly efficiency reports</p>
            </div>
            <input
              type="checkbox"
              checked={notifPrefs.whatsapp_enabled}
              onChange={(e) => setNotifPrefs({ ...notifPrefs, whatsapp_enabled: e.target.checked })}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">LPG Cylinder Refill Reminders</p>
              <p className="text-[11px] text-slate-400">Automated alerts when cylinder reaches below 15%</p>
            </div>
            <input
              type="checkbox"
              checked={notifPrefs.cylinder_refill_reminders}
              onChange={(e) => setNotifPrefs({ ...notifPrefs, cylinder_refill_reminders: e.target.checked })}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">Device Offline Detection</p>
              <p className="text-[11px] text-slate-400">Notifies you if the kitchen gas scale loses Wi-Fi</p>
            </div>
            <input
              type="checkbox"
              checked={notifPrefs.device_offline_alerts}
              onChange={(e) => setNotifPrefs({ ...notifPrefs, device_offline_alerts: e.target.checked })}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="pt-2 flex justify-end">
            <Button size="sm" onClick={handleSaveNotificationPrefs} isLoading={isSavingNotifs} leftIcon={<Save className="h-4 w-4" />}>
              Save Notification Preferences
            </Button>
          </div>
        </div>
      </Card>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 5. Safety Preferences Card                                         */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Shield className="h-4 w-4 text-danger" />
            Kitchen Safety Parameters
          </h3>
          {safetySuccessMsg && (
            <span className="text-xs text-green-600 font-bold flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" /> {safetySuccessMsg}
            </span>
          )}
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">Hardware Buzzer Alarm</p>
              <p className="text-[11px] text-slate-400">Audible alarm sound on scale hardware during elevated gas levels</p>
            </div>
            <input
              type="checkbox"
              checked={safetyPrefs.emergency_buzzer}
              onChange={(e) => setSafetyPrefs({ ...safetyPrefs, emergency_buzzer: e.target.checked })}
              className="h-5 w-5 accent-primary rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/50">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">Automated Emergency Valve Actuation</p>
              <p className="text-[11px] text-slate-400">Automatically command servo valve shut-off at &gt;= 1000 PPM (enforced)</p>
            </div>
            <input
              type="checkbox"
              checked={safetyPrefs.auto_shutoff_enabled}
              disabled
              className="h-5 w-5 accent-primary rounded cursor-not-allowed opacity-80"
              title="Essential protection - cannot be disabled"
            />
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-700/50 flex items-center justify-between">
            <div>
              <p className="font-bold text-slate-800 dark:text-slate-200">Warning Alert Threshold (PPM)</p>
              <p className="text-[11px] text-slate-400">PPM level to trigger warning notifications (Standard: 500 PPM)</p>
            </div>
            <select
              value={safetyPrefs.warning_threshold_ppm}
              onChange={(e) => setSafetyPrefs({ ...safetyPrefs, warning_threshold_ppm: Number(e.target.value) })}
              className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-800 dark:text-white"
            >
              <option value={300}>300 PPM (High Sensitivity)</option>
              <option value={400}>400 PPM</option>
              <option value={500}>500 PPM (Standard Recommended)</option>
              <option value={600}>600 PPM</option>
            </select>
          </div>

          <div className="pt-2 flex justify-end">
            <Button size="sm" onClick={handleSaveSafetyPrefs} isLoading={isSavingSafety} leftIcon={<Save className="h-4 w-4" />}>
              Save Safety Preferences
            </Button>
          </div>
        </div>
      </Card>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 6. Connected Device Settings Card                                  */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card>
        <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            Connected Devices & Hardware
          </h3>
        </div>

        {devices.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-4">No connected devices linked to your account.</p>
        ) : (
          <div className="space-y-3">
            {devices.map((device) => (
              <div
                key={device.id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/30 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Radio className="h-4 w-4 text-primary animate-pulse" />
                    <span className="font-bold text-slate-900 dark:text-white">{device.name}</span>
                    <span className="font-mono text-[10px] text-slate-400">({device.id})</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 text-[11px]">
                    <span className="flex items-center gap-1">
                      <Wifi className="h-3 w-3" />
                      {device.signal_strength ? `${device.signal_strength}%` : 'Connected'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Battery className="h-3 w-3" />
                      {device.battery_level ? `${device.battery_level}%` : 'AC Power'}
                    </span>
                    <span>Valve: <strong>{device.valve_status || 'OPEN'}</strong></span>
                  </div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                    device.status === 'active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-950/60 dark:text-green-300'
                      : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                  }`}
                >
                  {device.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 7. Dark Mode & Appearance                                          */}
      {/* ─────────────────────────────────────────────────────────────────── */}
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

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 8. Account Sign Out                                                */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <Card className="border-red-100 dark:border-red-950/40 bg-red-50/30 dark:bg-red-950/10">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-danger flex items-center gap-2">
              <Shield className="h-4 w-4" /> Sign Out of SafeGas AI
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              You will need to sign in with your email and password to access your account again.
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
