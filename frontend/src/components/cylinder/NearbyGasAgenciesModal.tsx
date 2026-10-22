import { useState, useEffect } from 'react'
import {
  MapPin,
  Phone,
  Navigation,
  ExternalLink,
  AlertCircle,
  Loader2,
  RefreshCw,
  Search,
  CheckCircle2,
  PhoneCall,
} from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { gasAgencyService } from '@/services/gasAgency.service'
import { normalizePhoneNumber } from '@/utils/phone'
import type { GasAgency } from '@/types'

interface NearbyGasAgenciesModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectAgencyForBooking?: (agencyName: string, phoneNumber?: string | null) => void
}

type SearchStatus =
  | 'idle'
  | 'requesting-location'
  | 'fetching'
  | 'success'
  | 'permission-denied'
  | 'no-results'
  | 'error'

export function NearbyGasAgenciesModal({
  isOpen,
  onClose,
  onSelectAgencyForBooking,
}: NearbyGasAgenciesModalProps) {
  const [status, setStatus] = useState<SearchStatus>('idle')
  const [agencies, setAgencies] = useState<GasAgency[]>([])
  const [errorMessage, setErrorMessage] = useState('')
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [radiusMeters, setRadiusMeters] = useState(10000)
  const [manualQuery, setManualQuery] = useState('')
  const [isSearchingManual, setIsSearchingManual] = useState(false)
  const [phoneAlert, setPhoneAlert] = useState<{ agencyId: string; message: string } | null>(null)

  // Start location flow whenever the modal opens
  useEffect(() => {
    if (isOpen) {
      handleRequestLocation()
      setPhoneAlert(null)
    } else {
      setPhoneAlert(null)
    }
  }, [isOpen])

  const handleRequestLocation = () => {
    setStatus('requesting-location')
    setErrorMessage('')

    if (!('geolocation' in navigator)) {
      setStatus('permission-denied')
      setErrorMessage('Geolocation is not supported by your browser.')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        }
        setUserLocation(coords)
        fetchAgencies(coords.latitude, coords.longitude, radiusMeters)
      },
      (error) => {
        console.warn('[NearbyGasAgencies] Geolocation error:', error.message)
        if (error.code === error.PERMISSION_DENIED) {
          setStatus('permission-denied')
          setErrorMessage('Location permission was denied. You can enter your area manually or search on Google Maps.')
        } else {
          setStatus('permission-denied')
          setErrorMessage('Unable to determine location. Please enter your area manually.')
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    )
  }

  const fetchAgencies = async (lat: number, lng: number, radius: number, query?: string) => {
    setStatus('fetching')
    setErrorMessage('')

    try {
      const data = await gasAgencyService.getNearbyAgencies(lat, lng, radius, query)
      if (data.agencies && data.agencies.length > 0) {
        setAgencies(data.agencies)
        setStatus('success')
      } else {
        setAgencies([])
        setStatus('no-results')
      }
    } catch (err: any) {
      console.error('[NearbyGasAgencies] API Error:', err)
      const detail = err.response?.data?.detail || err.message || 'Failed to fetch gas agencies.'
      setErrorMessage(detail)
      setStatus('error')
    }
  }

  const handleManualSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualQuery.trim()) return

    setIsSearchingManual(true)
    setErrorMessage('')

    try {
      const data = await gasAgencyService.searchAgencies(
        manualQuery.trim(),
        userLocation?.latitude,
        userLocation?.longitude,
        radiusMeters
      )

      if (data.agencies && data.agencies.length > 0) {
        setAgencies(data.agencies)
        setStatus('success')
      } else {
        setAgencies([])
        setStatus('no-results')
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Search failed.'
      setErrorMessage(detail)
      setStatus('error')
    } finally {
      setIsSearchingManual(false)
    }
  }

  const formatDistance = (km: number) => {
    if (km < 1) {
      return `${Math.round(km * 1000)} m away`
    }
    return `${km.toFixed(1)} km away`
  }

  const handleBookCylinderRefill = (agency: GasAgency) => {
    setPhoneAlert(null)
    const normalized = normalizePhoneNumber(agency.phone_number)

    if (!normalized) {
      setPhoneAlert({
        agencyId: agency.id,
        message: 'Phone number unavailable for this agency.',
      })
      return
    }

    if (onSelectAgencyForBooking) {
      onSelectAgencyForBooking(agency.name, normalized)
    }

    // Immediately open device phone dialler with the validated phone number prefilled
    window.location.href = `tel:${encodeURIComponent(normalized)}`
  }

  const getGoogleMapsSearchUrl = () => {
    if (manualQuery.trim()) {
      return `https://www.google.com/maps/search/LPG+gas+agency+in+${encodeURIComponent(manualQuery.trim())}`
    }
    if (userLocation) {
      return `https://www.google.com/maps/search/LPG+gas+agency/@${userLocation.latitude},${userLocation.longitude},13z`
    }
    return 'https://www.google.com/maps/search/LPG+gas+agency+near+me/'
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Nearby LPG Gas Agencies"
        description="Find verified LPG distributors, get directions, and call for refill inquiries."
      >
        <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
          {/* Search bar & Radius Controls */}
          <div className="flex flex-col sm:flex-row gap-2 items-center">
            <form onSubmit={handleManualSearch} className="flex-1 flex gap-2 w-full">
              <Input
                placeholder="Search city, area, or agency (e.g. Koramangala)"
                value={manualQuery}
                onChange={(e) => setManualQuery(e.target.value)}
                className="text-xs"
              />
              <Button type="submit" size="sm" variant="outline" isLoading={isSearchingManual}>
                <Search className="h-3.5 w-3.5" />
              </Button>
            </form>

            <div className="flex items-center gap-1.5 w-full sm:w-auto justify-end">
              <select
                value={radiusMeters}
                onChange={(e) => {
                  const newRad = Number(e.target.value)
                  setRadiusMeters(newRad)
                  if (userLocation) {
                    fetchAgencies(userLocation.latitude, userLocation.longitude, newRad, manualQuery || undefined)
                  }
                }}
                className="text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2.5 py-2 focus:ring-1 focus:ring-primary focus:outline-none"
              >
                <option value={5000}>5 km</option>
                <option value={10000}>10 km</option>
                <option value={15000}>15 km</option>
                <option value={20000}>20 km</option>
              </select>

              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={handleRequestLocation}
                title="Refresh with current GPS location"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {/* Loading States */}
          {(status === 'requesting-location' || status === 'fetching') && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                {status === 'requesting-location'
                  ? 'Requesting browser location permission...'
                  : `Searching for LPG gas agencies within ${radiusMeters / 1000} km...`}
              </p>
              <p className="text-[11px] text-slate-400">
                {status === 'requesting-location'
                  ? 'Please allow location access when prompted by your browser.'
                  : 'Retrieving verified distributors from Google Places.'}
              </p>
            </div>
          )}

          {/* Location Permission Denied State */}
          {status === 'permission-denied' && (
            <div className="p-5 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-center space-y-3">
              <div className="h-10 w-10 mx-auto rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                <MapPin className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-amber-900 dark:text-amber-200">
                Location Access Disabled
              </h4>
              <p className="text-xs text-amber-700 dark:text-amber-300 max-w-sm mx-auto">
                {errorMessage ||
                  'We could not access your device location. You can search manually by entering your city/area above or search on Google Maps.'}
              </p>

              <div className="pt-2 flex flex-wrap gap-2 justify-center">
                <Button size="sm" variant="outline" onClick={handleRequestLocation} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
                  Retry GPS Location
                </Button>
                <a
                  href={getGoogleMapsSearchUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-300 dark:border-slate-700 hover:bg-slate-50 shadow-xs"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Search on Google Maps
                </a>
              </div>
            </div>
          )}

          {/* API Error State */}
          {status === 'error' && (
            <div className="p-5 rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-center space-y-3">
              <div className="h-10 w-10 mx-auto rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 flex items-center justify-center">
                <AlertCircle className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-red-900 dark:text-red-200">
                Unable to Load Gas Agencies
              </h4>
              <p className="text-xs text-red-700 dark:text-red-300 max-w-sm mx-auto">
                {errorMessage}
              </p>

              <div className="pt-2 flex flex-wrap gap-2 justify-center">
                <Button size="sm" variant="outline" onClick={handleRequestLocation} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
                  Try Again
                </Button>
                <a
                  href={getGoogleMapsSearchUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-primary text-white hover:bg-primary-dark shadow-xs"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open in Google Maps
                </a>
              </div>
            </div>
          )}

          {/* No Results State */}
          {status === 'no-results' && (
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center space-y-3">
              <div className="h-10 w-10 mx-auto rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 flex items-center justify-center">
                <Search className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No Gas Agencies Found
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                No verified LPG cylinder agencies were found within {radiusMeters / 1000} km. Try increasing the search radius or explore directly on Google Maps.
              </p>

              <div className="pt-2 flex flex-wrap gap-2 justify-center">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const expanded = Math.min(20000, radiusMeters + 5000)
                    setRadiusMeters(expanded)
                    if (userLocation) {
                      fetchAgencies(userLocation.latitude, userLocation.longitude, expanded)
                    }
                  }}
                >
                  Expand Radius to {Math.min(20, (radiusMeters + 5000) / 1000)} km
                </Button>
                <a
                  href={getGoogleMapsSearchUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-primary text-white hover:bg-primary-dark shadow-xs"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Search Google Maps
                </a>
              </div>
            </div>
          )}

          {/* Success: List of Agency Cards */}
          {status === 'success' && agencies.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 px-1">
                <span>
                  Found <strong>{agencies.length}</strong> gas distributors within {radiusMeters / 1000} km
                </span>
                <span className="text-[11px]">Sorted by distance</span>
              </div>

              {agencies.map((agency) => (
                <div
                  key={agency.id}
                  className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-xs hover:border-primary/50 transition-colors space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-bold text-sm text-slate-900 dark:text-white leading-snug">
                          {agency.name}
                        </h4>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">
                          📍 {formatDistance(agency.distance_km)}
                        </span>
                        {agency.rating && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                            ★ {agency.rating.toFixed(1)}
                            {agency.user_ratings_total ? ` (${agency.user_ratings_total})` : ''}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-500 dark:text-slate-400 flex items-start gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span>{agency.address}</span>
                      </p>
                    </div>
                  </div>

                  {/* Phone Unavailable Alert for this agency */}
                  {phoneAlert?.agencyId === agency.id && (
                    <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2 animate-fadeIn">
                      <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
                      <span>{phoneAlert.message}</span>
                    </div>
                  )}

                  {/* Phone number and Action Buttons */}
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-700/60 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      {agency.phone_number ? (
                        <div className="flex items-center gap-1 text-slate-700 dark:text-slate-300 font-semibold text-xs">
                          <Phone className="h-3.5 w-3.5 text-primary" />
                          <span>{agency.phone_number}</span>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-400 italic">
                          Phone number not listed
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Book Cylinder Refill button — immediately opens phone dialler */}
                      <Button
                        size="sm"
                        onClick={() => handleBookCylinderRefill(agency)}
                        leftIcon={<PhoneCall className="h-3.5 w-3.5 text-white" />}
                        className="text-xs font-bold bg-primary hover:bg-primary-dark text-white shadow-xs"
                        title={agency.phone_number ? `Open phone dialler with ${agency.phone_number}` : 'Phone number unavailable'}
                      >
                        Book Cylinder Refill
                      </Button>

                      {/* Get Directions Button */}
                      <a
                        href={agency.google_maps_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-white hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                      >
                        <Navigation className="h-3.5 w-3.5 text-blue-500" />
                        Directions
                      </a>

                      {/* Optional: Select for Refill Booking */}
                      {onSelectAgencyForBooking && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onSelectAgencyForBooking(agency.name, agency.phone_number)
                            onClose()
                          }}
                          leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                          className="text-xs"
                        >
                          Select
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </>
  )
}
