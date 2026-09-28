import { useState, useEffect, useRef, useCallback } from 'react'
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
  Play,
  Square,
  RefreshCw,
  Flame,
  Wifi,
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
import { formatPPM, formatDateTime } from '@/utils/cn'
import { safetyService } from '@/services/safetyService'
import type {
  Device,
  GasReading,
  SafetyStatusResponse,
  ActiveLeakResponse,
  LeakHistoryResponse,
  DeviceDiagnosticsResponse,
  SimulatorStatusResponse,
} from '@/types'

export function Safety() {
  // Device context state
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  
  // Real backend safety states
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatusResponse | null>(null)
  const [diagnostics, setDiagnostics] = useState<DeviceDiagnosticsResponse | null>(null)
  const [gasReadings, setGasReadings] = useState<GasReading[]>([])
  const [activeLeak, setActiveLeak] = useState<ActiveLeakResponse | null>(null)
  const [leakHistory, setLeakHistory] = useState<LeakHistoryResponse | null>(null)
  const [simulatorStatus, setSimulatorStatus] = useState<SimulatorStatusResponse | null>(null)

  // Simulator control state
  const [simBaselinePpm, setSimBaselinePpm] = useState<number>(300)
  const [simMode, setSimMode] = useState<string>('fluctuate')
  const [isSimLoading, setIsSimLoading] = useState<boolean>(false)

  // Modal & Valve Action states
  const [showEmergencyModal, setShowEmergencyModal] = useState<boolean>(false)
  const [isValveActionLoading, setIsValveActionLoading] = useState<boolean>(false)

  // Overall page state
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Ref to prevent overlapping polling requests
  const isFetchingRef = useRef<boolean>(false)

  // ---------------------------------------------------------------------------
  // 1. Fetch user devices on mount
  // ---------------------------------------------------------------------------
  useEffect(() => {
    let isMounted = true
    async function loadDevices() {
      try {
        const userDevices = await safetyService.getDevices()
        if (isMounted) {
          setDevices(userDevices)
          if (userDevices.length > 0) {
            setSelectedDeviceId(userDevices[0].id)
          } else {
            setIsLoading(false)
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to fetch paired devices from backend')
          setIsLoading(false)
        }
      }
    }
    loadDevices()
    return () => {
      isMounted = false
    }
  }, [])

  // ---------------------------------------------------------------------------
  // 2. Main Data Refresh Function for Selected Device
  // ---------------------------------------------------------------------------
  const refreshSafetyData = useCallback(async (deviceId: string, showSpinner = false) => {
    if (!deviceId || isFetchingRef.current) return
    isFetchingRef.current = true

    if (showSpinner) setIsLoading(true)
    setError(null)

    try {
      const [
        safetyRes,
        diagnosticsRes,
        readingsRes,
        activeLeakRes,
        leakHistRes,
        simStatusRes,
      ] = await Promise.all([
        safetyService.getSafetyStatus(deviceId).catch(() => null),
        safetyService.getDiagnostics(deviceId).catch(() => null),
        safetyService.getGasReadings(deviceId, 100).catch(() => []),
        safetyService.getActiveLeak(deviceId).catch(() => null),
        safetyService.getLeakHistory(deviceId, 100).catch(() => ({ leaks: [] })),
        safetyService.getSimulatorStatus(deviceId).catch(() => null),
      ])

      setSafetyStatus(safetyRes)
      setDiagnostics(diagnosticsRes)
      setGasReadings(readingsRes)
      setActiveLeak(activeLeakRes)
      setLeakHistory(leakHistRes)
      setSimulatorStatus(simStatusRes)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to connect to Safety Service')
    } finally {
      setIsLoading(false)
      isFetchingRef.current = false
    }
  }, [])

  // ---------------------------------------------------------------------------
  // 3. Trigger initial fetch & 3s polling for safety telemetry
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedDeviceId) return

    refreshSafetyData(selectedDeviceId, true)

    const intervalId = setInterval(() => {
      refreshSafetyData(selectedDeviceId, false)
    }, 3000)

    return () => {
      clearInterval(intervalId)
    }
  }, [selectedDeviceId, refreshSafetyData])

  // ---------------------------------------------------------------------------
  // 4. Simulator Handlers
  // ---------------------------------------------------------------------------
  const handleStartSimulator = async () => {
    if (!selectedDeviceId) return
    setIsSimLoading(true)
    try {
      await safetyService.startSimulator({
        device_id: selectedDeviceId,
        baseline_ppm: simBaselinePpm,
        mode: simMode,
        interval_seconds: 1.0,
      })
      await refreshSafetyData(selectedDeviceId)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start simulator')
    } finally {
      setIsSimLoading(false)
    }
  }

  const handleStopSimulator = async () => {
    if (!selectedDeviceId) return
    setIsSimLoading(true)
    try {
      await safetyService.stopSimulator(selectedDeviceId)
      await refreshSafetyData(selectedDeviceId)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to stop simulator')
    } finally {
      setIsSimLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Solenoid Valve Action Handlers
  // ---------------------------------------------------------------------------
  const handleConfirmValveAction = async () => {
    if (!selectedDeviceId || !safetyStatus) return
    setIsValveActionLoading(true)
    setShowEmergencyModal(false)

    try {
      if (safetyStatus.valve_status === 'CLOSED') {
        await safetyService.resetValve(selectedDeviceId)
      } else {
        await safetyService.emergencyCloseValve(selectedDeviceId)
      }
      await refreshSafetyData(selectedDeviceId)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update valve status')
    } finally {
      setIsValveActionLoading(false)
    }
  }

  // Prepare chart data in chronological order (oldest -> newest)
  const chartData = [...gasReadings].reverse().map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    ppm: r.ppm_value,
    status: r.status,
    source: r.source || 'IOT',
  }))

  const isValveOpen = safetyStatus?.valve_status !== 'CLOSED'
  const currentPpm = safetyStatus?.latest_gas_ppm ?? null
  const backendStatus = safetyStatus?.status || 'normal'

  return (
    <div className="space-y-6">
      {/* Header Banner & Device Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-red-100 dark:bg-red-950/40 text-danger flex items-center justify-center shrink-0">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Safety & Gas Leak Monitoring</h2>
              {backendStatus && gasStatusBadge(backendStatus === 'critical' ? 'danger' : backendStatus === 'warning' ? 'warning' : 'safe')}
              {simulatorStatus?.running && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 animate-pulse">
                  SIMULATOR ACTIVE
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Live Telemetry &bull; Single-Source Backend Architecture Active
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {devices.length > 0 && (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="text-xs font-semibold px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-800 dark:text-slate-200 focus:outline-none"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.id})
                </option>
              ))}
            </select>
          )}

          <Button
            variant={isValveOpen ? 'danger' : 'primary'}
            onClick={() => setShowEmergencyModal(true)}
            isLoading={isValveActionLoading}
            leftIcon={<Power className="h-4 w-4" />}
            disabled={!selectedDeviceId}
          >
            {isValveOpen ? 'Emergency Valve Shutoff' : 'Re-open Solenoid Valve'}
          </Button>
        </div>
      </div>

      {/* Error state alert */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
          <Button size="sm" variant="ghost" onClick={() => refreshSafetyData(selectedDeviceId, true)}>
            Retry
          </Button>
        </div>
      )}

      {/* No devices state */}
      {!isLoading && devices.length === 0 && (
        <Card className="text-center py-10 space-y-3">
          <Radio className="h-10 w-10 text-slate-400 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">No Paired Devices Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Please navigate to the Devices page and pair an IoT sensor device to start viewing telemetry and safety status.
          </p>
        </Card>
      )}

      {/* Main Content (when device selected) */}
      {selectedDeviceId && (
        <>
          {/* Active Leak Alert Banner (if backend reports active leak) */}
          {activeLeak && (
            <div className="p-4 rounded-2xl bg-red-600 text-white border border-red-700 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-pulse">
              <div className="flex items-center gap-3">
                <Flame className="h-8 w-8 text-yellow-300 shrink-0" />
                <div>
                  <h3 className="text-sm font-extrabold uppercase tracking-wide">
                    CRITICAL: ACTIVE GAS LEAK DETECTED ({activeLeak.peak_ppm} PPM)
                  </h3>
                  <p className="text-xs text-red-100 mt-0.5">
                    Started at: {formatDateTime(activeLeak.start_time)} &bull; Auto-shutoff triggered: {activeLeak.auto_shutoff_triggered ? 'YES' : 'NO'}
                  </p>
                </div>
              </div>
              <div className="px-3 py-1 rounded-xl bg-red-800 text-red-100 text-xs font-mono font-bold">
                LEAK EVENT #{activeLeak.id}
              </div>
            </div>
          )}

          {/* Grid Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Current Gas PPM"
              value={currentPpm !== null ? formatPPM(currentPpm) : 'N/A'}
              subtitle={
                backendStatus === 'critical'
                  ? 'CRITICAL THRESHOLD EXCEEDED (>= 1000 PPM)'
                  : backendStatus === 'warning'
                  ? 'WARNING LEVEL ELEVATED (500–999 PPM)'
                  : 'NORMAL (< 500 PPM)'
              }
              icon={
                <Radio
                  className={`h-5 w-5 ${
                    backendStatus === 'critical'
                      ? 'text-red-500 animate-ping'
                      : backendStatus === 'warning'
                      ? 'text-amber-500 animate-pulse'
                      : 'text-green-500 animate-pulse'
                  }`}
                />
              }
              color={
                backendStatus === 'critical'
                  ? 'text-red-600'
                  : backendStatus === 'warning'
                  ? 'text-amber-500'
                  : 'text-green-500'
              }
            />

            <StatCard
              title="Solenoid Valve Status"
              value={safetyStatus?.valve_status ? `${safetyStatus.valve_status} (${isValveOpen ? 'Normal' : 'Shutoff'})` : 'UNKNOWN'}
              subtitle="Software State from Backend"
              icon={<Zap className="h-5 w-5 text-primary" />}
              color={isValveOpen ? 'text-primary' : 'text-danger'}
            />

            <StatCard
              title="Sensor Health & Diagnostics"
              value={diagnostics?.sensor?.health || 'Healthy'}
              subtitle={`Battery: ${diagnostics?.sensor?.battery_level ?? '92'}% | Signal: ${diagnostics?.sensor?.signal_strength ?? '-65'}dBm`}
              icon={<Activity className="h-5 w-5 text-blue-500" />}
              color="text-blue-500"
            />
          </div>

          {/* Real-time Backend Gas PPM Graph */}
          <Card>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
              <div>
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  Live Gas PPM Graph (Persisted Backend Readings)
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Device: <span className="font-mono">{selectedDeviceId}</span> &bull; Source:{' '}
                  <span className="font-semibold">{diagnostics?.telemetry?.source || (chartData.length > 0 ? chartData[chartData.length - 1].source : 'IOT')}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => refreshSafetyData(selectedDeviceId)}>
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
                <span className="text-xs font-bold text-green-500 flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-green-500 animate-ping" /> Live
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              {chartData.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 space-y-2">
                  <Activity className="h-8 w-8 text-slate-300" />
                  <span>Waiting for telemetry data from backend...</span>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 'dataMax + 100']} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        borderColor: '#334155',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '12px',
                      }}
                      formatter={(val: any, _name: any, item: any) => [
                        `${val} PPM (Source: ${item.payload.source})`,
                        'Gas PPM',
                      ]}
                    />
                    <ReferenceLine
                      y={500}
                      label={{ value: 'Warning Threshold (500 PPM)', fill: '#f59e0b', fontSize: 10 }}
                      stroke="#f59e0b"
                      strokeDasharray="4 4"
                    />
                    <ReferenceLine
                      y={1000}
                      label={{ value: 'Critical Threshold (1000 PPM)', fill: '#dc2626', fontSize: 10 }}
                      stroke="#dc2626"
                      strokeDasharray="4 4"
                    />
                    <Line
                      type="monotone"
                      dataKey="ppm"
                      stroke="#16a34a"
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>

          {/* Dev Mode Telemetry Simulator Controls */}
          <Card className="border-purple-200 dark:border-purple-900/40 bg-purple-50/30 dark:bg-purple-950/10">
            <div className="flex items-center justify-between border-b border-purple-100 dark:border-purple-900/40 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-lg bg-purple-100 dark:bg-purple-950/60 text-purple-600 flex items-center justify-center shrink-0">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-xs font-extrabold text-purple-900 dark:text-purple-200 uppercase tracking-wider">
                    Dev Mode Telemetry Simulator (Development Only)
                  </h3>
                  <p className="text-[11px] text-purple-600 dark:text-purple-400 mt-0.5">
                    Routes generated telemetry through canonical backend ingestion pipeline with source="SIMULATOR"
                  </p>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                  simulatorStatus?.running
                    ? 'bg-purple-600 text-white animate-pulse'
                    : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                }`}
              >
                {simulatorStatus?.running ? `RUNNING (${simulatorStatus.generated_count} read)` : 'STOPPED'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs items-end">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Baseline PPM</label>
                <input
                  type="number"
                  value={simBaselinePpm}
                  onChange={(e) => setSimBaselinePpm(Number(e.target.value))}
                  disabled={simulatorStatus?.running}
                  className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none font-mono"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Pattern Mode</label>
                <select
                  value={simMode}
                  onChange={(e) => setSimMode(e.target.value)}
                  disabled={simulatorStatus?.running}
                  className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="fluctuate">Fluctuate (Normal ~300 PPM)</option>
                  <option value="increase">Gradual Increase (+50/step)</option>
                  <option value="decrease">Gradual Decrease (-20/step)</option>
                  <option value="spike">Critical Spike (+250/step &gt; 1000)</option>
                </select>
              </div>

              <div className="sm:col-span-2 flex gap-2">
                <Button
                  variant="primary"
                  onClick={handleStartSimulator}
                  disabled={simulatorStatus?.running || isSimLoading}
                  isLoading={isSimLoading && !simulatorStatus?.running}
                  leftIcon={<Play className="h-4 w-4" />}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 border-none text-white"
                >
                  Start Simulator
                </Button>
                <Button
                  variant="outline"
                  onClick={handleStopSimulator}
                  disabled={!simulatorStatus?.running || isSimLoading}
                  isLoading={isSimLoading && simulatorStatus?.running}
                  leftIcon={<Square className="h-4 w-4" />}
                  className="flex-1"
                >
                  Stop Simulator
                </Button>
              </div>
            </div>
          </Card>

          {/* Sensor Diagnostics & Leak Events Timeline */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Diagnostics Card */}
            <Card>
              <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Backend Sensor Diagnostics
                </h3>
              </div>

              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> Sensor Core
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {diagnostics?.sensor?.health || 'MQ6 (Healthy)'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Battery className="h-4 w-4 text-blue-500" /> Battery Level
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {diagnostics?.sensor?.battery_level !== undefined ? `${diagnostics.sensor.battery_level}%` : '92%'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Wifi className="h-4 w-4 text-purple-500" /> Signal Strength
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 font-mono">
                    {diagnostics?.sensor?.signal_strength !== undefined ? `${diagnostics.sensor.signal_strength} dBm` : '-65 dBm'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Calendar className="h-4 w-4 text-slate-400" /> Connection Status
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 uppercase">
                    {diagnostics?.connection?.status || 'ONLINE'}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 text-[11px] text-slate-500 dark:text-slate-400">
                  ℹ️ Fail-safe active: Software auto-shutoff valve triggers automatically when telemetry exceeds 1000 PPM.
                </div>
              </div>
            </Card>

            {/* Historical Leak Events Timeline (2 Cols) */}
            <Card className="lg:col-span-2">
              <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Leak Incidents & History Timeline (Backend Database Records)
                </h3>
              </div>

              <div className="space-y-3">
                {(!leakHistory || leakHistory.leaks.length === 0) ? (
                  <div className="py-8 text-center text-xs text-slate-400">
                    No historical gas leak incidents recorded for this device.
                  </div>
                ) : (
                  leakHistory.leaks.map((event) => (
                    <div
                      key={event.id}
                      className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-slate-900 dark:text-white">
                            Peak PPM: {event.peak_ppm} PPM
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
                          Started: {formatDateTime(event.start_time)}{' '}
                          {event.end_time ? `| Resolved: ${formatDateTime(event.end_time)}` : '| (Active)'}
                        </p>
                      </div>

                      <div className="text-right font-mono text-[11px] text-slate-500">
                        Event #{event.id}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </>
      )}

      {/* Emergency Valve Toggle Modal */}
      <Modal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        title={isValveOpen ? 'Confirm Emergency Valve Shutoff?' : 'Re-open Solenoid Valve?'}
        description={
          isValveOpen
            ? 'This will immediately issue an EMERGENCY_CLOSE command to the backend for this device.'
            : 'Ensure there are no active gas leaks in your kitchen before reopening the valve.'
        }
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEmergencyModal(false)}>
              Cancel
            </Button>
            <Button
              variant={isValveOpen ? 'danger' : 'primary'}
              onClick={handleConfirmValveAction}
              isLoading={isValveActionLoading}
            >
              {isValveOpen ? 'Shut Off Valve Now' : 'Re-open Valve'}
            </Button>
          </>
        }
      >
        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>This action updates the backend device software valve status authoritative record.</span>
        </div>
      </Modal>
    </div>
  )
}
