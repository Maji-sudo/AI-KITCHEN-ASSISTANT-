import { useState } from 'react'
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
import { mockGasReadings, mockCurrentPPM, mockLeakEvents } from '@/utils/mockData'
import { formatPPM, formatDateTime } from '@/utils/cn'

export function Safety() {
  const [isShutoffActive, setIsShutoffActive] = useState(true)
  const [showEmergencyModal, setShowEmergencyModal] = useState(false)
  const [ppmValue] = useState(mockCurrentPPM)

  const chartData = mockGasReadings.map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    ppm: r.ppm_value,
  }))

  const handleToggleValve = () => {
    setIsShutoffActive((prev) => !prev)
    setShowEmergencyModal(false)
  }

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
              {gasStatusBadge(ppmValue < 200 ? 'safe' : 'warning')}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              MQ6 Sensor Live Telemetry &bull; Sub-3s Leak Pipeline Active
            </p>
          </div>
        </div>

        <Button
          variant={isShutoffActive ? 'danger' : 'primary'}
          onClick={() => setShowEmergencyModal(true)}
          leftIcon={<Power className="h-4 w-4" />}
        >
          {isShutoffActive ? 'Emergency Valve Shutoff' : 'Re-open Solenoid Valve'}
        </Button>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Current Gas PPM"
          value={formatPPM(ppmValue)}
          subtitle="Safe Threshold: < 200 PPM"
          icon={<Radio className="h-5 w-5 text-green-500 animate-pulse" />}
          color="text-green-500"
        />

        <StatCard
          title="Solenoid Valve Status"
          value={isShutoffActive ? 'OPEN (Normal)' : 'CLOSED (Shutoff)'}
          subtitle="Servo Auto-Actuation Enabled"
          icon={<Zap className="h-5 w-5 text-primary" />}
          color={isShutoffActive ? 'text-primary' : 'text-danger'}
        />

        <StatCard
          title="MQ6 Sensor Health"
          value="100% Calibrated"
          subtitle="Battery: 92% | Signal: -65dBm"
          icon={<Activity className="h-5 w-5 text-blue-500" />}
          color="text-blue-500"
        />
      </div>

      {/* Real-time Recharts PPM Graph */}
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
          <div>
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Live Gas PPM Graph (Last 30 Mins)
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Continuous telemetry sampling every 3 seconds</p>
          </div>
          <span className="text-xs font-bold text-green-500 flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-ping" /> Live
          </span>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 400]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                formatter={(val: any) => [`${val} PPM`, 'Gas PPM']}
              />
              <ReferenceLine y={200} label={{ value: 'Warning threshold (200 PPM)', fill: '#f59e0b', fontSize: 10 }} stroke="#f59e0b" strokeDasharray="4 4" />
              <ReferenceLine y={1000} label={{ value: 'Danger threshold (1000 PPM)', fill: '#dc2626', fontSize: 10 }} stroke="#dc2626" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="ppm" stroke="#16a34a" strokeWidth={2.5} dot={false} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
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
              <span className="font-bold text-slate-800 dark:text-slate-200">MQ6 (Healthy)</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Battery className="h-4 w-4 text-blue-500" /> Backup Battery
              </span>
              <span className="font-bold text-slate-800 dark:text-slate-200">92% (Good)</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-slate-400" /> Last Calibration
              </span>
              <span className="font-bold text-slate-800 dark:text-slate-200">Jul 10, 2026</span>
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
            {mockLeakEvents.map((event) => (
              <div
                key={event.id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
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
                    Detected: {formatDateTime(event.start_time)}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Duration: 4 mins
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Emergency Valve Toggle Modal */}
      <Modal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        title={isShutoffActive ? 'Confirm Valve Shutoff?' : 'Re-open Solenoid Valve?'}
        description={
          isShutoffActive
            ? 'This will immediately trigger the ESP32 servo motor to shut off the LPG cylinder valve.'
            : 'Ensure there are no active gas leaks in your kitchen before reopening the valve.'
        }
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEmergencyModal(false)}>
              Cancel
            </Button>
            <Button variant={isShutoffActive ? 'danger' : 'primary'} onClick={handleToggleValve}>
              {isShutoffActive ? 'Shut Off Valve Now' : 'Re-open Valve'}
            </Button>
          </>
        }
      >
        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>Manual overrides send high-priority WebSocket signals to your paired ESP32 controller.</span>
        </div>
      </Modal>
    </div>
  )
}
