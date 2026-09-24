import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ShieldAlert,
  Flame,
  Zap,
  Sparkles,
  TrendingDown,
  Calendar,
  AlertTriangle,
  ArrowRight,
  Clock,
  Radio,
  PlusCircle,
  Bell,
  Cpu,
  RefreshCw,
  Sliders,
  CheckCircle2,
  Layers,
  Wrench,
} from 'lucide-react'
import { Card, StatCard } from '@/components/ui/Card'
import { Gauge } from '@/components/ui/Gauge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { categoryBadge, gasStatusBadge } from '@/components/ui/Badge'
import { deviceService } from '@/services/device.service'
import { refillService } from '@/services/refill.service'
import { simulationService } from '@/services/simulation.service'
import { analyticsService } from '@/services/analytics.service'
import {
  mockEfficiencyScore,
  mockRecommendations,
  mockNotifications,
} from '@/utils/mockData'
import { formatGrams, formatPPM, getCylinderColor, getScoreColor } from '@/utils/cn'

export function Dashboard() {
  const queryClient = useQueryClient()
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const [simMessage, setSimMessage] = useState<string | null>(null)
  const [showManualModal, setShowManualModal] = useState(false)
  const [manualType, setManualType] = useState<'gas' | 'weight' | 'leak' | 'cooking'>('gas')

  // Manual input form states
  const [manualPpm, setManualPpm] = useState(185)
  const [manualWeightG, setManualWeightG] = useState(24500)
  const [manualPeakPpm, setManualPeakPpm] = useState(1100)
  const [manualCookingDish, setManualCookingDish] = useState('Dal Tadka & Rice')
  const [manualCookingDuration, setManualCookingDuration] = useState(25)
  const [manualCookingGas, setManualCookingGas] = useState(85)
  const [manualSubmitting, setManualSubmitting] = useState(false)

  // 1. Fetch user's devices
  const { data: devices = [], isLoading: isLoadingDevices } = useQuery({
    queryKey: ['devices'],
    queryFn: deviceService.getDevices,
  })

  // Determine active device
  const activeDevice = devices.find((d) => d.id === selectedDeviceId) || devices[0] || null

  // 2. Fetch device telemetry
  const { data: gasReadings = [] } = useQuery({
    queryKey: ['gasReadings', activeDevice?.id],
    queryFn: () => (activeDevice ? deviceService.getGasReadings(activeDevice.id, 10) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  const { data: weightReadings = [] } = useQuery({
    queryKey: ['weightReadings', activeDevice?.id],
    queryFn: () => (activeDevice ? deviceService.getWeightReadings(activeDevice.id, 5) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  const { data: cylinders = [] } = useQuery({
    queryKey: ['cylinders', activeDevice?.id],
    queryFn: () => (activeDevice ? deviceService.getCylinders(activeDevice.id) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  const { data: refillPred } = useQuery({
    queryKey: ['refillPrediction', activeDevice?.id],
    queryFn: () => (activeDevice ? refillService.getLatestPrediction(activeDevice.id) : Promise.resolve(null)),
    enabled: !!activeDevice,
  })

  const { data: dailyAnalytics = [] } = useQuery({
    queryKey: ['dailyAnalytics', activeDevice?.id],
    queryFn: () => (activeDevice ? analyticsService.getAnalytics(activeDevice.id, 'daily', 7) : Promise.resolve([])),
    enabled: !!activeDevice,
  })

  // Computed metrics
  const latestGas = gasReadings[0]
  const currentPPM = latestGas?.ppm_value ?? 180
  const gasStatus: import('@/types').GasStatus = currentPPM >= 1000 ? 'critical' : currentPPM >= 200 ? 'warning' : 'safe'

  const activeCylinder = cylinders[0]
  const tareWeight = activeCylinder?.tare_weight_g ?? 15300
  const fullWeight = activeCylinder?.full_weight_g ?? 29500
  const netCapacity = fullWeight - tareWeight // ~14200g
  const latestWeight = weightReadings[0]?.weight_g ?? fullWeight
  const remainingNetG = Math.max(0, latestWeight - tareWeight)
  const cylinderPercentage = Math.min(100, Math.max(0, Math.round((remainingNetG / netCapacity) * 100)))

  const daysLeft = refillPred?.days_left ?? 25
  const predictedEmptyDate = refillPred?.predicted_empty_date
    ? new Date(refillPred.predicted_empty_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
    : 'In ~25 days'

  const lastDay = dailyAnalytics[dailyAnalytics.length - 1]
  const todayConsumption = lastDay?.consumption_g ?? 310
  const activeRecs = mockRecommendations.filter((r) => r.status === 'active')


  // Handler: Create simulated device
  const handleCreateSimulatedDevice = async () => {
    setIsSimulating(true)
    setSimMessage(null)
    try {
      const dev = await simulationService.createSimulatedDevice(
        'Kitchen SafeGas Hub',
        '14.2kg'
      )
      // Automatically generate 7 days of realistic usage
      await simulationService.generateData(dev.id, 7, 'medium')
      setSelectedDeviceId(dev.id)
      setSimMessage('Simulated device created with 7 days of realistic telemetry!')
      await queryClient.invalidateQueries()
    } catch (err: any) {
      setSimMessage(err?.response?.data?.detail || 'Failed to create simulated device')
    } finally {
      setIsSimulating(false)
    }
  }

  // Handler: Trigger usage simulation
  const handleGenerateData = async (pattern: string) => {
    if (!activeDevice) return
    setIsSimulating(true)
    setSimMessage(null)
    try {
      const res = await simulationService.generateData(activeDevice.id, 7, pattern)
      setSimMessage(res.message)
      await queryClient.invalidateQueries()
    } catch (err: any) {
      setSimMessage(err?.response?.data?.detail || 'Failed to simulate data')
    } finally {
      setIsSimulating(false)
    }
  }

  // Handler: Trigger safety scenario
  const handleSafetyScenario = async (scenario: 'normal' | 'warning' | 'critical') => {
    if (!activeDevice) return
    setIsSimulating(true)
    setSimMessage(null)
    try {
      const res = await simulationService.triggerSafety(activeDevice.id, scenario)
      setSimMessage(res.message)
      await queryClient.invalidateQueries()
    } catch (err: any) {
      setSimMessage(err?.response?.data?.detail || 'Failed to execute safety scenario')
    } finally {
      setIsSimulating(false)
    }
  }

  // Handler: Reset data
  const handleResetData = async () => {
    if (!activeDevice) return
    setIsSimulating(true)
    setSimMessage(null)
    try {
      const res = await simulationService.resetData(activeDevice.id)
      setSimMessage(res.message)
      await queryClient.invalidateQueries()
    } catch (err: any) {
      setSimMessage(err?.response?.data?.detail || 'Failed to reset data')
    } finally {
      setIsSimulating(false)
    }
  }

  // Handler: Submit manual telemetry
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeDevice) return
    setManualSubmitting(true)
    try {
      if (manualType === 'gas') {
        await simulationService.manualGas(activeDevice.id, Number(manualPpm))
      } else if (manualType === 'weight') {
        await simulationService.manualWeight(activeDevice.id, Number(manualWeightG))
      } else if (manualType === 'leak') {
        await simulationService.manualGas(activeDevice.id, Number(manualPeakPpm), 'critical')
      } else if (manualType === 'cooking') {
        await simulationService.manualCooking(
          activeDevice.id,
          Number(manualCookingDuration),
          Number(manualCookingGas),
          manualCookingDish
        )
      }
      await queryClient.invalidateQueries()
      setShowManualModal(false)
      setSimMessage(`Manual ${manualType} reading successfully recorded!`)
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to submit manual data')
    } finally {
      setManualSubmitting(false)
    }
  }

  // ----------------------------------------------------
  // EMPTY STATE: NO DEVICE CONNECTED
  // ----------------------------------------------------
  if (!isLoadingDevices && (!devices || devices.length === 0)) {
    return (
      <div className="space-y-6">
        {/* Onboarding Banner */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 border border-slate-700/80 shadow-2xl text-white">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/20 border border-primary/30 text-primary text-xs font-bold">
              <Radio className="h-3.5 w-3.5 animate-pulse" />
              SafeGas AI Smart Kitchen Environment
            </div>

            <h1 className="text-3xl font-black tracking-tight">
              No SafeGas device connected yet.
            </h1>

            <p className="text-sm text-slate-300 leading-relaxed">
              SafeGas AI continuously monitors LPG cylinder weight, detects gas leaks in sub-3 seconds,
              tracks cooking energy usage, and predicts cylinder refill dates.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <Button
                onClick={handleCreateSimulatedDevice}
                isLoading={isSimulating}
                leftIcon={<Cpu className="h-4 w-4" />}
                className="shadow-xl shadow-primary/30"
              >
                Provision Simulated Device &amp; Data
              </Button>

              <Link to="/devices">
                <Button variant="outline" className="border-slate-600 text-slate-200 hover:text-white">
                  Pair Physical ESP32 Hardware
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Informational Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card className="space-y-2">
            <ShieldAlert className="h-8 w-8 text-primary" />
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Sub-3s Leak Pipeline</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time MQ6 gas sensor monitoring with automatic solenoid emergency valve shutoff.
            </p>
          </Card>

          <Card className="space-y-2">
            <Flame className="h-8 w-8 text-amber-500" />
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Cylinder Load Cell</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Gram-accurate load cell telemetry tracks net LPG consumption with automated refill forecasting.
            </p>
          </Card>

          <Card className="space-y-2">
            <Sparkles className="h-8 w-8 text-blue-500" />
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">AI Kitchen Assistant</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Gemini-powered cooking recommendations, gas conservation tips, and recipe gas tracking.
            </p>
          </Card>
        </div>
      </div>
    )
  }

  // ----------------------------------------------------
  // ACTIVE DASHBOARD WITH DEVICE & REAL TELEMETRY
  // ----------------------------------------------------
  return (
    <div className="space-y-6">
      {/* Top Banner Alert depending on current gas status */}
      <div
        className={`p-4 rounded-2xl text-white shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
          gasStatus === 'critical'
            ? 'bg-gradient-to-r from-red-600 to-rose-700 shadow-red-500/30'
            : gasStatus === 'warning'
            ? 'bg-gradient-to-r from-amber-500 to-orange-600 shadow-amber-500/20'
            : 'bg-gradient-to-r from-green-500 to-emerald-600 shadow-green-500/20'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0">
            <Radio className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-extrabold">
              {gasStatus === 'critical'
                ? 'CRITICAL ALERT: Gas Leak Threshold Exceeded!'
                : gasStatus === 'warning'
                ? 'WARNING: Elevated Gas PPM Detected'
                : 'All Kitchen Systems Operational'}
            </h2>
            <p className="text-xs text-white/90 mt-0.5">
              Live PPM: <strong>{formatPPM(currentPPM)}</strong> &bull; Cylinder Level:{' '}
              <strong>{cylinderPercentage}%</strong> ({daysLeft} days remaining) &bull; Device:{' '}
              <span className="font-mono">{activeDevice?.name || activeDevice?.id}</span>
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {devices.length > 1 && (
            <select
              value={activeDevice?.id}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              aria-label="Select SafeGas Device"
              className="bg-white/20 text-white rounded-lg text-xs font-semibold px-2 py-1 outline-none border-0"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id} className="text-slate-900">
                  {d.name} ({d.id})
                </option>
              ))}
            </select>
          )}

          <Link to="/safety">
            <Button size="sm" variant="secondary" className="bg-white/20 hover:bg-white/30 text-white border-0">
              Safety Live Monitor
            </Button>
          </Link>
        </div>
      </div>

      {/* Dev Simulation & Manual Input Bar (Development only) */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white shadow-xl space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Sliders className="h-3.5 w-3.5 text-primary" />
              Development Simulator &amp; Data Input Controls
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowManualModal(true)}
              className="h-7 text-xs border-slate-700 hover:border-slate-500 text-slate-200"
              leftIcon={<Wrench className="h-3 w-3" />}
            >
              Manual Data Entry
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleResetData}
              isLoading={isSimulating}
              className="h-7 text-xs text-danger hover:bg-red-950/40"
              leftIcon={<RefreshCw className="h-3 w-3" />}
            >
              Reset Data
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
          <span className="text-[11px] text-slate-400 font-semibold">Simulate Scenarios:</span>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleGenerateData('medium')}
            isLoading={isSimulating}
            className="h-7 bg-slate-800 hover:bg-slate-700 text-[11px]"
          >
            📊 7-Day Normal Usage
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleGenerateData('high')}
            isLoading={isSimulating}
            className="h-7 bg-slate-800 hover:bg-slate-700 text-[11px]"
          >
            🔥 7-Day High Usage
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleSafetyScenario('normal')}
            isLoading={isSimulating}
            className="h-7 bg-green-950/40 hover:bg-green-900/50 text-green-300 border border-green-800/40 text-[11px]"
          >
            ✅ Normal (180 PPM)
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleSafetyScenario('warning')}
            isLoading={isSimulating}
            className="h-7 bg-amber-950/40 hover:bg-amber-900/50 text-amber-300 border border-amber-800/40 text-[11px]"
          >
            ⚠️ Warning (350 PPM)
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleSafetyScenario('critical')}
            isLoading={isSimulating}
            className="h-7 bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-800/40 text-[11px]"
          >
            🚨 Critical Leak (1050 PPM)
          </Button>
        </div>

        {simMessage && (
          <div className="text-xs text-primary font-semibold flex items-center gap-1.5 pt-1">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {simMessage}
          </div>
        )}
      </div>

      {/* Grid Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Safety Status"
          value={gasStatusBadge(gasStatus)}
          subtitle={`Gas PPM: ${formatPPM(currentPPM)}`}
          icon={<ShieldAlert className="h-5 w-5 text-green-600 dark:text-green-400" />}
          color="text-green-600 dark:text-green-400"
        />

        <StatCard
          title="Today's Consumption"
          value={formatGrams(todayConsumption)}
          subtitle="Dynamic daily LPG burn"
          icon={<Flame className="h-5 w-5 text-amber-500" />}
          color="text-amber-500"
          trend={{ value: -8, label: 'vs yesterday' }}
        />

        <StatCard
          title="Refill Prediction"
          value={`${daysLeft} Days`}
          subtitle={`Predicted Empty: ${predictedEmptyDate}`}
          icon={<Calendar className="h-5 w-5 text-blue-500" />}
          color="text-blue-500"
        />

        <StatCard
          title="Efficiency Score"
          value={`${mockEfficiencyScore.overall_score} / 100`}
          subtitle="Top 15% of households"
          icon={<Zap className="h-5 w-5 text-primary" />}
          color="text-primary"
          trend={{ value: 8, label: 'this week' }}
        />
      </div>

      {/* Main Row: Gauges & Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cylinder Gauge Card */}
        <Card className="flex flex-col items-center justify-between text-center">
          <div className="w-full flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Flame className="h-4 w-4 text-amber-500" />
              Cylinder Capacity
            </h3>
            <Link to="/cylinder" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <Gauge
            value={cylinderPercentage}
            size={160}
            strokeWidth={14}
            color={getCylinderColor(cylinderPercentage)}
            label={`${cylinderPercentage}%`}
            sublabel={`${formatGrams(remainingNetG)} remaining`}
          />

          <div className="w-full mt-6 grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-700/40 p-3 rounded-xl">
            <div>
              <span className="text-slate-400 block text-[10px]">Tare (Empty)</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">{formatGrams(tareWeight)}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Current Total</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">{formatGrams(latestWeight)}</span>
            </div>
          </div>

          <Link to="/cylinder" className="w-full mt-4">
            <Button className="w-full" size="sm">
              Book Refill Now
            </Button>
          </Link>
        </Card>

        {/* Efficiency Breakdown Card */}
        <Card className="flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              Efficiency Index
            </h3>
            <Link to="/efficiency" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              Score Breakdown <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="flex items-center justify-center my-2">
            <Gauge
              value={mockEfficiencyScore.overall_score}
              size={140}
              strokeWidth={12}
              color={getScoreColor(mockEfficiencyScore.overall_score)}
              label={`${mockEfficiencyScore.overall_score}`}
              sublabel="Overall Grade A"
            />
          </div>

          <div className="space-y-2 mt-4 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">Safety Compliance</span>
              <span className="font-bold text-slate-900 dark:text-white">
                {gasStatus === 'safe' ? '98%' : gasStatus === 'warning' ? '70%' : '25%'}
              </span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${gasStatus === 'safe' ? 'bg-green-500' : 'bg-amber-500'}`}
                style={{ width: gasStatus === 'safe' ? '98%' : '70%' }}
              />
            </div>

            <div className="flex justify-between items-center pt-1">
              <span className="text-slate-600 dark:text-slate-400">Gas Burn Optimization</span>
              <span className="font-bold text-slate-900 dark:text-white">78%</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
              <div className="bg-primary h-full rounded-full" style={{ width: '78%' }} />
            </div>
          </div>
        </Card>

        {/* Quick Actions & AI Insights */}
        <Card className="flex flex-col justify-between">
          <div className="border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Kitchen Tools
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <Link to="/cooking" className="p-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary transition-colors flex flex-col items-center text-center gap-1.5">
              <PlusCircle className="h-6 w-6" />
              <span className="text-xs font-bold">Log Cooking</span>
            </Link>
            <Link to="/cooking" className="p-3 rounded-xl bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/30 dark:hover:bg-blue-900/40 text-blue-600 dark:text-blue-400 transition-colors flex flex-col items-center text-center gap-1.5">
              <Sparkles className="h-6 w-6" />
              <span className="text-xs font-bold">AI Assistant</span>
            </Link>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700">
            <p className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5 mb-1">
              <TrendingDown className="h-4 w-4 text-green-500" />
              Gas Saving Tip
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
              Pre-soaking lentils and covering cooking pots reduces flame burn duration by up to 22%.
            </p>
          </div>
        </Card>
      </div>

      {/* Lower Row: Recommendations & Recent Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Recommendations */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Active Recommendations ({activeRecs.length})
            </h3>
            <Link to="/recommendations" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {activeRecs.slice(0, 3).map((rec) => (
              <div
                key={rec.id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-700/40 border border-slate-100 dark:border-slate-700/80 flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {categoryBadge(rec.category)}
                    <span className="text-[10px] font-bold text-slate-400">
                      {Math.round(rec.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-200 font-medium">{rec.message}</p>
                </div>
                <Link to="/recommendations">
                  <Button size="sm" variant="outline" className="text-xs h-8 shrink-0">
                    Review
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </Card>

        {/* Notifications Digest */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700/60 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Bell className="h-4 w-4 text-blue-500" />
              Recent Alerts
            </h3>
            <Link to="/notifications" className="text-xs font-semibold text-primary hover:underline">
              All
            </Link>
          </div>

          <div className="space-y-3">
            {mockNotifications.slice(0, 3).map((n) => (
              <div key={n.id} className="flex items-start gap-2.5 text-xs border-b border-slate-100 dark:border-slate-700/50 pb-2.5 last:border-0 last:pb-0">
                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">{n.payload.title}</p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">{n.payload.body}</p>
                  <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
                    <Clock className="h-3 w-3" />
                    {new Date(n.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Manual Data Input Modal */}
      <Modal
        isOpen={showManualModal}
        onClose={() => setShowManualModal(false)}
        title="Manual SafeGas Telemetry Input"
        description="Enter sensor readings directly into the backend ingestion pipeline for testing without IoT hardware."
      >
        <form onSubmit={handleManualSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Input Category
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(['gas', 'weight', 'leak', 'cooking'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setManualType(t)}
                  className={`py-1.5 text-xs font-bold rounded-lg border transition-all ${
                    manualType === t
                      ? 'bg-primary text-white border-primary shadow-md shadow-primary/20'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                  }`}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {manualType === 'gas' && (
            <div>
              <Input
                type="number"
                label="Gas PPM Value"
                value={manualPpm}
                onChange={(e) => setManualPpm(Number(e.target.value))}
                placeholder="e.g. 185"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1">Normal: &lt;200 PPM | Warning: 200–999 | Critical: &ge;1000</p>
            </div>
          )}

          {manualType === 'weight' && (
            <div>
              <Input
                type="number"
                label="Cylinder Gross Weight (grams)"
                value={manualWeightG}
                onChange={(e) => setManualWeightG(Number(e.target.value))}
                placeholder="e.g. 24500"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1">Full: ~29,500g | Tare (empty): ~15,300g</p>
            </div>
          )}

          {manualType === 'leak' && (
            <div>
              <Input
                type="number"
                label="Peak PPM Level"
                value={manualPeakPpm}
                onChange={(e) => setManualPeakPpm(Number(e.target.value))}
                placeholder="e.g. 1100"
                required
              />
              <p className="text-[11px] text-red-500 mt-1">This will automatically trigger auto-shutoff and emergency notifications.</p>
            </div>
          )}

          {manualType === 'cooking' && (
            <div className="space-y-3">
              <Input
                label="Dish Name"
                value={manualCookingDish}
                onChange={(e) => setManualCookingDish(e.target.value)}
                placeholder="e.g. Dal Tadka"
                required
              />
              <div className="grid grid-cols-2 gap-3">
                <Input
                  type="number"
                  label="Duration (mins)"
                  value={manualCookingDuration}
                  onChange={(e) => setManualCookingDuration(Number(e.target.value))}
                  required
                />
                <Input
                  type="number"
                  label="Gas Consumed (grams)"
                  value={manualCookingGas}
                  onChange={(e) => setManualCookingGas(Number(e.target.value))}
                  required
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-700">
            <Button type="button" variant="outline" onClick={() => setShowManualModal(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={manualSubmitting}>
              Submit to Ingestion Pipeline
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
