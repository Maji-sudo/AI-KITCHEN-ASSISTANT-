import { useState, useEffect } from 'react'
import {
  Flame,
  Calendar,
  CheckCircle2,
  Clock,
  Truck,
  Plus,
  MapPin,
} from 'lucide-react'
import { Card, StatCard } from '@/components/ui/Card'
import { Gauge } from '@/components/ui/Gauge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useQuery } from '@tanstack/react-query'
import { deviceService } from '@/services/device.service'
import { refillService } from '@/services/refill.service'
import { formatGrams, formatDateTime, getCylinderColor } from '@/utils/cn'
import { normalizePhoneNumber } from '@/utils/phone'
import { bookingService } from '@/services/booking.service'
import { NearbyGasAgenciesModal } from '@/components/cylinder/NearbyGasAgenciesModal'
import type { Booking } from '@/types'

export function Cylinder() {
  const [showBookingModal, setShowBookingModal] = useState(false)
  const [showAgenciesModal, setShowAgenciesModal] = useState(false)
  const [distributor, setDistributor] = useState('HP Gas - Koramangala Agency')
  const [customAgencyPhone, setCustomAgencyPhone] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [bookingSuccess, setBookingSuccess] = useState(false)
  const [bookings, setBookings] = useState<Booking[]>([])
  const [isLoadingBookings, setIsLoadingBookings] = useState(true)
  const [bookingError, setBookingError] = useState('')
  const [cancellingBookingId, setCancellingBookingId] = useState<number | null>(null)

  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: deviceService.getDevices,
  })

  const activeDevice = devices[0] || null

  const { data: cylinders = [] } = useQuery({
    queryKey: ['cylinders', activeDevice?.id],
    queryFn: () => (activeDevice ? deviceService.getCylinders(activeDevice.id) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  const { data: weightReadings = [] } = useQuery({
    queryKey: ['weightReadings', activeDevice?.id],
    queryFn: () => (activeDevice ? deviceService.getWeightReadings(activeDevice.id, 1) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  const { data: refillPred } = useQuery({
    queryKey: ['refillPrediction', activeDevice?.id],
    queryFn: () => (activeDevice ? refillService.getLatestPrediction(activeDevice.id) : Promise.resolve(null)),
    enabled: !!activeDevice,
  })

  // Fetch real bookings from backend on mount (called unconditionally)
  useEffect(() => {
    bookingService.getBookings()
      .then(setBookings)
      .catch(() => setBookings([]))
      .finally(() => setIsLoadingBookings(false))
  }, [])

  // Handle loading state
  if (!activeDevice || !cylinders[0] || !refillPred) {
    return (
      <div className="py-12 flex items-center justify-center text-sm text-slate-500 animate-pulse font-medium">
        Loading cylinder telemetry and predictions from backend...
      </div>
    )
  }

  const cylinderData = cylinders[0]
  const tareWeight = cylinderData.tare_weight_g || 15300
  const fullWeight = cylinderData.full_weight_g || 29500
  const netCapacity = fullWeight - tareWeight
  const latestWeight = weightReadings[0]?.weight_g ?? fullWeight
  const netRemaining = Math.max(0, latestWeight - tareWeight)
  const cylinderPercentage = Math.min(100, Math.max(0, Math.round((netRemaining / netCapacity) * 100)))

  const prediction = refillPred

  const handleBookRefill = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setBookingError('')

    try {
      const newBooking = await bookingService.createBooking({
        device_id: activeDevice?.id || 'SGD-001',
        distributor,
        booking_date: new Date().toISOString(),
        source: 'app',
      })
      // Immediately prepend the new booking to the list
      setBookings((prev) => [newBooking, ...prev])
      setBookingSuccess(true)
      
      // HP Gas or Selected Agency Phone Handoff via tel: dialler
      if (distributor === 'HP Gas - Koramangala Agency') {
        const hpGasNumber = import.meta.env.VITE_HP_GAS_REFILL_NUMBER || '+919493602222'
        const normalized = normalizePhoneNumber(hpGasNumber)
        if (normalized) {
          window.location.href = `tel:${encodeURIComponent(normalized)}`
        }
      } else if (customAgencyPhone) {
        const normalized = normalizePhoneNumber(customAgencyPhone)
        if (normalized) {
          window.location.href = `tel:${encodeURIComponent(normalized)}`
        }
      } else {
        setTimeout(() => {
          setBookingSuccess(false)
          setShowBookingModal(false)
        }, 2000)
      }
    } catch {
      setBookingError('Failed to create booking. Please ensure the backend is running.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelBooking = async (bookingId: number) => {
    setCancellingBookingId(bookingId)

    try {
      const updatedBooking = await bookingService.cancelBooking(bookingId)

      setBookings((prev) =>
        prev.map((booking) =>
          booking.id === bookingId ? updatedBooking : booking
        )
      )
    } catch (error) {
      console.error('Failed to cancel booking:', error)
      setBookingError('Failed to cancel booking. Please try again.')
    } finally {
      setCancellingBookingId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-amber-100 dark:bg-amber-950/40 text-amber-500 flex items-center justify-center shrink-0">
            <Flame className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Cylinder & Refill Management</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Monitor remaining LPG weight and AI refill forecasting.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            onClick={() => setShowAgenciesModal(true)}
            leftIcon={<MapPin className="h-4 w-4 text-primary" />}
          >
            Find Nearby Gas Agencies
          </Button>

          <Button
            onClick={() => setShowBookingModal(true)}
            leftIcon={<Truck className="h-4 w-4" />}
          >
            Book Cylinder Refill
          </Button>
        </div>
      </div>

      {/* Grid Overview Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Large Gauge Card */}
        <Card className="flex flex-col items-center justify-center text-center p-8">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-6">
            Current LPG Level
          </h3>

          <Gauge
            value={cylinderPercentage}
            size={200}
            strokeWidth={16}
            color={getCylinderColor(cylinderPercentage)}
            label={`${cylinderPercentage}%`}
            sublabel={`${formatGrams(netRemaining)} Net Gas`}
          />

          <div className="mt-8 grid grid-cols-2 gap-4 w-full text-xs border-t border-slate-100 dark:border-slate-700/60 pt-6">
            <div className="text-left">
              <span className="text-slate-400 block text-[11px]">Installed Date</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {new Date(cylinderData.install_date).toLocaleDateString('en-IN', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            </div>
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Cylinder Type</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{cylinderData.cylinder_type} Standard</span>
            </div>
          </div>
        </Card>

        {/* Prediction & Refill Specs */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <StatCard
              title="Estimated Days Remaining"
              value={`${prediction.days_left} Days`}
              subtitle={`Predicted Empty: ${new Date(prediction.predicted_empty_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}`}
              icon={<Clock className="h-5 w-5 text-amber-500" />}
              color="text-amber-500"
            />

            <StatCard
              title="Refill Confidence Score"
              value={`${Math.round(prediction.confidence * 100)}%`}
              subtitle="Weighted moving average forecast"
              icon={<CheckCircle2 className="h-5 w-5 text-primary" />}
              color="text-primary"
            />
          </div>

          <Card>
            <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Physical Specifications & Weights
              </h3>
            </div>

            <div className="grid grid-cols-3 gap-4 text-xs text-center">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Empty Tare Weight</span>
                <span className="text-base font-extrabold text-slate-800 dark:text-slate-200 mt-1 block">
                  {formatGrams(tareWeight)}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Current Net Gas</span>
                <span className="text-base font-extrabold text-amber-500 mt-1 block">
                  {formatGrams(netRemaining)}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Full Capacity Gross</span>
                <span className="text-base font-extrabold text-slate-800 dark:text-slate-200 mt-1 block">
                  {formatGrams(fullWeight)}
                </span>
              </div>
            </div>
          </Card>
        </div>

      </div>

      {/* Refill History & Orders */}
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Truck className="h-4 w-4 text-primary" />
            Cylinder Booking & Refill History
            {!isLoadingBookings && (
              <span className="ml-1 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-[10px] font-bold">
                {bookings.length} records
              </span>
            )}
          </h3>
          <Button size="sm" variant="outline" onClick={() => setShowBookingModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
            New Booking
          </Button>
        </div>

        <div className="space-y-3">
          {isLoadingBookings ? (
            <div className="py-8 text-center text-xs text-slate-400 animate-pulse">
              Loading bookings from database...
            </div>
          ) : bookings.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No bookings yet. Click <strong>"New Booking"</strong> to create your first refill order.
            </div>
          ) : (
            bookings.map((b) => (
              <div
                key={b.id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white">{b.distributor}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        b.status === 'delivered'
                          ? 'bg-green-100 text-green-700 dark:bg-green-950/60 dark:text-green-400'
                          : b.status === 'cancelled'
                          ? 'bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-400'
                          : 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
                      }`}
                    >
                      {b.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] mt-1 flex items-center gap-1">
                    <Calendar className="h-3 w-3" /> Booked: {formatDateTime(b.booking_date)}
                  </p>
                </div>

                <div className="text-right flex flex-col items-end gap-2">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                    Source: {b.source.toUpperCase()}
                  </span>
                  {b.status === 'pending' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleCancelBooking(b.id)}
                      isLoading={cancellingBookingId === b.id}
                 >
                      Cancel
                  </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Book Refill Modal */}
      <Modal
        isOpen={showBookingModal}
        onClose={() => {
          if (!isSubmitting) {
            setShowBookingModal(false)
            setBookingError('')
          }
        }}
        title="Book Cylinder Refill"
        description="Select your LPG distributor to schedule a refill order."
      >
        {bookingSuccess ? (
          <div className="py-8 flex flex-col items-center text-center text-green-600">
            <CheckCircle2 className="h-12 w-12 mb-2 animate-bounce" />
            <h4 className="text-base font-extrabold">
              {distributor === 'HP Gas - Koramangala Agency' ? 'Booking Initiated! ✅' : 'Booking Saved to Database! ✅'}
            </h4>
            {distributor === 'HP Gas - Koramangala Agency' ? (
              <div className="mt-2 text-xs text-slate-500 space-y-3">
                <p>Booking initiated. Please complete the HP Gas missed call from your registered mobile number.</p>
                <p>
                  <strong>Did the dialer not open?</strong><br />
                  Call manually: <a href={`tel:${import.meta.env.VITE_HP_GAS_REFILL_NUMBER || '+919493602222'}`} className="text-primary font-bold hover:underline">{import.meta.env.VITE_HP_GAS_REFILL_NUMBER || '+919493602222'}</a>
                </p>
                <Button className="mt-4" variant="outline" size="sm" onClick={() => { setBookingSuccess(false); setShowBookingModal(false); }}>
                  Close
                </Button>
              </div>
            ) : (
              <p className="text-xs text-slate-500 mt-1">Your distributor will process your refill order shortly.</p>
            )}
          </div>
        ) : (
          <form onSubmit={handleBookRefill} className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  LPG Distributor Agency
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setShowBookingModal(false)
                    setShowAgenciesModal(true)
                  }}
                  className="text-xs text-primary font-bold hover:underline flex items-center gap-1"
                >
                  <MapPin className="h-3 w-3" /> Find Nearby
                </button>
              </div>

              <select
                value={distributor}
                onChange={(e) => setDistributor(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3.5 py-2 text-sm focus:ring-2 focus:ring-primary focus:outline-none"
              >
                {distributor &&
                  !['HP Gas - Koramangala Agency', 'Indane Gas - Indiranagar', 'Bharatgas - HSR Layout'].includes(distributor) && (
                    <option value={distributor}>{distributor} (Nearby)</option>
                  )}
                <option value="HP Gas - Koramangala Agency">HP Gas - Koramangala Agency</option>
                <option value="Indane Gas - Indiranagar">Indane Gas - Indiranagar</option>
                <option value="Bharatgas - HSR Layout">Bharatgas - HSR Layout</option>
              </select>
            </div>

            <div>
              <Input label="Target Delivery Address" defaultValue="No 42, 4th Cross, Koramangala, Bengaluru" />
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 text-xs text-slate-500">
              💡 Estimated delivery time: 1-2 working days. Estimated price: ₹803 per 14.2kg cylinder.
            </div>

            {bookingError && (
              <p className="text-xs text-red-500 font-semibold">{bookingError}</p>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => { setShowBookingModal(false); setBookingError('') }}>
                Cancel
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                Confirm Order
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Nearby Gas Agencies Finder Modal */}
      <NearbyGasAgenciesModal
        isOpen={showAgenciesModal}
        onClose={() => setShowAgenciesModal(false)}
        onSelectAgencyForBooking={(agencyName, phone) => {
          setDistributor(agencyName)
          setCustomAgencyPhone(phone || null)
          setShowBookingModal(true)
        }}
      />
    </div>
  )
}

