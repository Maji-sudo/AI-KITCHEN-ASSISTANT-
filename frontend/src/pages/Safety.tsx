import { useState, useEffect } from 'react'
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Radio,
  Power,
  Battery,
  Activity,
  Calendar,
  Zap,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts'
import { Card, StatCard } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { gasStatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { formatPPM, formatDateTime, formatTime } from '@/utils/cn'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { deviceService } from '@/services/device.service'
import { safetyService } from '@/services/safetyService'
import { API_BASE } from '@/services/apiClient'

export function Safety() {
  const queryClient = useQueryClient()
  const [showEmergencyModal, setShowEmergencyModal] = useState(false)

  const { data: devices = [], isLoading: isLoadingDevices } = useQuery({
    queryKey: ['devices'],
    queryFn: deviceService.getDevices,
  })

  const activeDevice = devices[0] || null

  const { data: safetyStatus, isLoading: isLoadingSafety } = useQuery({
    queryKey: ['safetyStatus', activeDevice?.id],
    queryFn: () => safetyService.getSafetyStatus(activeDevice!.id),
    enabled: !!activeDevice,
    refetchInterval: 5000,
  })

  const { data: gasReadings = [], isLoading: isLoadingReadings } = useQuery({
    queryKey: ['gasReadings', activeDevice?.id],
    queryFn: () => safetyService.getGasReadings(activeDevice!.id, 30),
    enabled: !!activeDevice,
    refetchInterval: 5000,
  })

  const { data: leakHistoryData, isLoading: isLoadingLeaks } = useQuery({
    queryKey: ['leakEvents', activeDevice?.id],
    queryFn: () => safetyService.getLeakHistory(activeDevice!.id),
    enabled: !!activeDevice,
  })

  const { data: activeLeak, isLoading: isLoadingActiveLeak } = useQuery({
    queryKey: ['activeLeak', activeDevice?.id],
    queryFn: () => safetyService.getActiveLeak(activeDevice!.id),
    enabled: !!activeDevice,
    refetchInterval: 5000,
  })

  const { data: diagnostics, isLoading: isLoadingDiag } = useQuery({
    queryKey: ['diagnostics', activeDevice?.id],
    queryFn: () => safetyService.getDiagnostics(activeDevice!.id),
    enabled: !!activeDevice,
  })

  const emergencyCloseMutation = useMutation({
    mutationFn: () => safetyService.emergencyCloseValve(activeDevice!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus', activeDevice?.id] })
      queryClient.invalidateQueries({ queryKey: ['diagnostics', activeDevice?.id] })
      queryClient.invalidateQueries({ queryKey: ['activeLeak', activeDevice?.id] })
      setShowEmergencyModal(false)
    },
  })

  const resetValveMutation = useMutation({
    mutationFn: () => safetyService.resetValve(activeDevice!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus', activeDevice?.id] })
      queryClient.invalidateQueries({ queryKey: ['diagnostics', activeDevice?.id] })
      queryClient.invalidateQueries({ queryKey: ['activeLeak', activeDevice?.id] })
      setShowEmergencyModal(false)
    },
  })

  // Phase 5: Real-time Updates via Server-Sent Events (SSE)
  useEffect(() => {
    if (!activeDevice) return

    const token = localStorage.getItem('access_token')
    const url = `${API_BASE}/devices/${activeDevice.id}/safety/stream?token=${token}`
    
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'SAFETY_UPDATE') {
          // 1. Update safety status directly in cache
          queryClient.setQueryData(['safetyStatus', activeDevice.id], payload.data)
          
          // 2. Append to gas readings for the real-time chart
          if (payload.data.latest_gas_ppm !== null) {
            queryClient.setQueryData(['gasReadings', activeDevice.id], (old: any) => {
              const newReading = {
                id: Date.now(),
                device_id: activeDevice.id,
                timestamp: payload.data.timestamp || new Date().toISOString(),
                ppm_value: payload.data.latest_gas_ppm,
                status: payload.data.status,
                source: payload.data.source || 'IOT',
              }
              const current = Array.isArray(old) ? old : []
              const filtered = current.filter((r: any) => r.timestamp !== newReading.timestamp)
              const updated = [...filtered, newReading]
              if (updated.length > 30) return updated.slice(updated.length - 30)
              return updated
            })
          }

          // 3. Selectively invalidate leaks/diagnostics if status crossed a critical threshold
          // In a production app, we would compare with old status, but this ensures safety
          if (payload.data.status === 'critical' || payload.data.valve_status === 'CLOSED') {
            queryClient.invalidateQueries({ queryKey: ['activeLeak', activeDevice.id] })
            queryClient.invalidateQueries({ queryKey: ['leakEvents', activeDevice.id] })
            queryClient.invalidateQueries({ queryKey: ['diagnostics', activeDevice.id] })
          } else if (payload.data.status === 'normal') {
             // Invalidate to pick up leak resolution
             queryClient.invalidateQueries({ queryKey: ['activeLeak', activeDevice.id] })
          }
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE Connection Error:', err)
      eventSource.close() // Close and rely on standard HTTP polling fallback
    }

    return () => {
      eventSource.close()
    }
  }, [activeDevice, queryClient])

  if (isLoadingDevices) {
    return <div className="p-8 text-center text-slate-500">Loading device...</div>
  }

  if (!activeDevice) {
    return <div className="p-8 text-center text-slate-500">No device selected or available.</div>
  }

  const isLoadingAll = isLoadingSafety || isLoadingReadings || isLoadingLeaks || isLoadingDiag || isLoadingActiveLeak

  if (isLoadingAll && !safetyStatus) {
    return <div className="p-8 text-center text-slate-500">Loading safety data...</div>
  }

  const ppmValue = safetyStatus?.latest_gas_ppm ?? 0
  const isShutoffActive = safetyStatus?.valve_status === 'CLOSED'
  
  // Create chart data sorted chronologically ascending
  const displayReadings = [...gasReadings].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
  const chartData = displayReadings.map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    ppm: Number(r.ppm_value),
  }))

  const displayLeaks = leakHistoryData?.leaks || []

  const handleToggleValve = async () => {
    if (isShutoffActive) {
      resetValveMutation.mutate()
    } else {
      emergencyCloseMutation.mutate()
    }
  }

  const isToggling = emergencyCloseMutation.isPending || resetValveMutation.isPending

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-red-100 dark:bg-red-950/40 text-danger flex items-center justify-center shrink-0">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Safety & Gas Leak Monitoring</h2>
              {gasStatusBadge(safetyStatus?.status || 'normal')}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex flex-wrap items-center gap-1.5">
              <span>MQ6 Sensor Telemetry &bull; Device: <span className="font-mono">{activeDevice.name}</span></span>
              {safetyStatus?.source && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
                  {safetyStatus.source === 'SIMULATOR' ? '🧪 Simulator' : safetyStatus.source === 'MANUAL' ? '✍️ Manual Entry' : '📡 ESP32 Sensor'}
                </span>
              )}
              {safetyStatus?.connection_status === 'offline' && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                  ⚠️ Telemetry Stale / Offline (Last seen: {safetyStatus.last_seen ? formatTime(safetyStatus.last_seen) : 'unknown'})
                </span>
              )}
            </p>
          </div>
        </div>

        <Button
          variant={isShutoffActive ? 'primary' : 'danger'}
          onClick={() => setShowEmergencyModal(true)}
          disabled={isToggling || safetyStatus?.valve_status === 'unknown'}
          leftIcon={<Power className="h-4 w-4" />}
        >
          {isToggling ? 'Processing...' : isShutoffActive ? 'Re-open Solenoid Valve' : 'Emergency Valve Shutoff'}
        </Button>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Current Gas PPM"
          value={safetyStatus?.latest_gas_ppm !== null && safetyStatus?.latest_gas_ppm !== undefined ? formatPPM(safetyStatus.latest_gas_ppm) : 'No Data'}
          subtitle={
            safetyStatus?.connection_status === 'offline'
              ? `⚠️ Offline (Last: ${safetyStatus.last_seen ? formatTime(safetyStatus.last_seen) : 'Unknown'})`
              : `Safe Threshold: < 500 PPM • ${safetyStatus?.source === 'SIMULATOR' ? 'Simulator' : safetyStatus?.source === 'MANUAL' ? 'Manual' : 'ESP32'}`
          }
          icon={<Radio className={`h-5 w-5 ${ppmValue >= 1000 ? 'text-danger animate-ping' : ppmValue >= 500 ? 'text-amber-500 animate-pulse' : 'text-green-500'}`} />}
          color={ppmValue >= 1000 ? 'text-danger' : ppmValue >= 500 ? 'text-amber-500' : 'text-green-500'}
        />

        <StatCard
          title="Solenoid Valve Status"
          value={safetyStatus?.valve_status === 'CLOSED' ? 'CLOSED (Shutoff)' : safetyStatus?.valve_status === 'OPEN' ? 'OPEN (Normal)' : 'Unknown'}
          subtitle="Servo Auto-Actuation Enabled"
          icon={<Zap className={`h-5 w-5 ${safetyStatus?.valve_status === 'CLOSED' ? 'text-danger' : 'text-primary'}`} />}
          color={safetyStatus?.valve_status === 'CLOSED' ? 'text-danger' : 'text-primary'}
        />

        <StatCard
          title="MQ6 Sensor Health"
          value={diagnostics?.sensor.health === 'healthy' ? 'Healthy' : diagnostics?.sensor.health || 'Not available'}
          subtitle={`Battery: ${diagnostics?.sensor.battery_level ?? 'N/A'}% | Signal: ${diagnostics?.connection.signal_strength ?? 'N/A'}dBm`}
          icon={<Activity className={`h-5 w-5 ${diagnostics?.sensor.health === 'healthy' ? 'text-blue-500' : 'text-slate-400'}`} />}
          color={diagnostics?.sensor.health === 'healthy' ? 'text-blue-500' : 'text-slate-500'}
        />
      </div>

      {/* Real-time Recharts PPM Graph */}
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <div>
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Live Gas PPM Graph
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Continuous telemetry sampling</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400">
              {safetyStatus?.timestamp ? `Updated ${formatTime(safetyStatus.timestamp)}` : ''}
            </span>
            <span className={`text-xs font-bold flex items-center gap-1 ${safetyStatus?.connection_status === 'offline' ? 'text-amber-500' : 'text-green-500'}`}>
              <span className={`h-2 w-2 rounded-full ${safetyStatus?.connection_status === 'offline' ? 'bg-amber-500' : 'bg-green-500 animate-ping'}`} />
              {safetyStatus?.connection_status === 'offline' ? 'Offline' : 'Live'}
            </span>
          </div>
        </div>

        <div className="h-72 w-full pt-2">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  domain={[0, (dataMax: number) => Math.max(1200, Math.ceil((Number(dataMax) || 0) * 1.15))]}
                  tickFormatter={(val: number) => `${Math.round(val)}`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  formatter={(val: any) => [`${val} PPM`, 'Gas PPM']}
                />
                <ReferenceLine y={500} label={{ value: 'Warning (500 PPM)', fill: '#f59e0b', fontSize: 10 }} stroke="#f59e0b" strokeDasharray="4 4" />
                <ReferenceLine y={1000} label={{ value: 'Critical (1000 PPM)', fill: '#dc2626', fontSize: 10 }} stroke="#dc2626" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="ppm"
                  stroke={ppmValue >= 1000 ? '#dc2626' : ppmValue >= 500 ? '#f59e0b' : '#16a34a'}
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full w-full flex items-center justify-center text-sm text-slate-400">
              No recent telemetry data available.
            </div>
          )}
        </div>
      </Card>

      {/* Sensor Diagnostics & Leak Events Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Diagnostics Card */}
        <Card>
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Sensor Diagnostics
            </h3>
          </div>

          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> Sensor Core
              </span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {diagnostics?.sensor.health === 'healthy' ? 'MQ6 (Healthy)' : diagnostics?.sensor.health || 'Not available'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Battery className="h-4 w-4 text-blue-500" /> Backup Battery
              </span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {diagnostics?.sensor.battery_level ? `${diagnostics.sensor.battery_level}% (Good)` : 'Not available'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-slate-400" /> Last Calibration
              </span>
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {diagnostics?.sensor.calibration_date ? formatDateTime(diagnostics.sensor.calibration_date) : 'Not available'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 text-[11px] text-slate-500 dark:text-slate-400">
              ℹ️ Fail-safe active: Even if WiFi loses connection, local ESP32 firmware auto-shuts off solenoid valve if PPM &gt; 1000.
            </div>
          </div>
        </Card>

        {/* Historical Leak Events Timeline (2 Cols) */}
        <Card className="lg:col-span-2">
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Leak Incidents & History Timeline
            </h3>
          </div>

          <div className="space-y-4">
            {activeLeak?.active && (
              <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-amber-900 dark:text-amber-100">
                      Peak PPM: {formatPPM(activeLeak.peak_ppm)}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 animate-pulse">
                      Active Leak
                    </span>
                  </div>
                  <p className="text-amber-700 dark:text-amber-400/80 text-[11px] mt-1">
                    Detected: {formatDateTime(activeLeak.start_time)}
                  </p>
                </div>
              </div>
            )}

            {displayLeaks.length > 0 || activeLeak?.active ? (
              displayLeaks
                .filter((event) => !activeLeak?.active || event.start_time !== activeLeak.start_time)
                .map((event) => (
                  <div
                    key={event.id}
                    className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 dark:text-white">
                          Peak PPM: {formatPPM(event.peak_ppm)}
                        </span>
                        {event.auto_shutoff_triggered && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-400">
                            Auto-Shutoff Triggered
                          </span>
                        )}
                        {event.false_alarm && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300">
                            False Alarm
                          </span>
                        )}
                      </div>
                      <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-1">
                        Detected: {formatDateTime(event.start_time)}
                        {event.end_time ? ` | Resolved: ${formatDateTime(event.end_time)}` : ''}
                      </p>
                    </div>
                  </div>
                ))
            ) : (
              <div className="text-sm text-slate-400 py-4 text-center">
                No leak incidents recorded.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Emergency Valve Toggle Modal */}
      <Modal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        title={isShutoffActive ? 'Re-open Solenoid Valve?' : 'Confirm Valve Shutoff?'}
        description={
          isShutoffActive
            ? 'Ensure there are no active gas leaks in your kitchen before reopening the valve.'
            : 'This will immediately issue an emergency command to shut off the LPG cylinder valve.'
        }
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEmergencyModal(false)} disabled={isToggling}>
              Cancel
            </Button>
            <Button 
              variant={isShutoffActive ? 'primary' : 'danger'} 
              onClick={handleToggleValve}
              disabled={isToggling}
            >
              {isToggling ? 'Processing...' : isShutoffActive ? 'Re-open Valve' : 'Shut Off Valve Now'}
            </Button>
          </>
        }
      >
        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>Manual overrides send high-priority commands to your paired controller.</span>
        </div>
      </Modal>
    </div>
  )
}
