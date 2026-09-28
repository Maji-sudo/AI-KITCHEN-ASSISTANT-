import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Cpu,
  Plus,
  Wifi,
  Battery,
  Trash2,
  Radio,
  Sliders,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { deviceStatusBadge } from '@/components/ui/Badge'
import { deviceService } from '@/services/device.service'
import { simulationService } from '@/services/simulation.service'

export function Devices() {
  const queryClient = useQueryClient()
  const [showPairModal, setShowPairModal] = useState(false)
  const [newDeviceId, setNewDeviceId] = useState('')
  const [newDeviceName, setNewDeviceName] = useState('')
  const [isPairing, setIsPairing] = useState(false)
  const [isSimulating, setIsSimulating] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const { data: devices = [], isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: deviceService.getDevices,
  })

  const handlePairDevice = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newDeviceId || !newDeviceName) return
    setIsPairing(true)
    setErrorMessage('')

    try {
      await deviceService.pairDevice(newDeviceId.trim(), newDeviceName.trim())
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
      setNewDeviceId('')
      setNewDeviceName('')
      setShowPairModal(false)
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || 'Failed to pair device.')
    } finally {
      setIsPairing(false)
    }
  }

  const handleCreateSimulatedDevice = async () => {
    setIsSimulating(true)
    setErrorMessage('')
    try {
      const dev = await simulationService.createSimulatedDevice('Kitchen SafeGas Hub', '14.2kg')
      await simulationService.generateData(dev.id, 7, 'medium')
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || 'Failed to create simulated device.')
    } finally {
      setIsSimulating(false)
    }
  }

  const handleRemoveDevice = async (id: string) => {
    if (!confirm(`Are you sure you want to remove device ${id}?`)) return
    try {
      await deviceService.removeDevice(id)
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to remove device.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 card-shadow">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-purple-100 dark:bg-purple-950/40 text-purple-600 flex items-center justify-center shrink-0">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Paired SafeGas IoT Devices</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Manage ESP32 gas &amp; weight sensor hardware or simulated units paired to your account.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => setShowPairModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Pair New Device
          </Button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-xs font-semibold">
          {errorMessage}
        </div>
      )}

      {/* Devices Grid */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-400">Loading paired devices...</div>
      ) : devices.length === 0 ? (
        <Card className="py-12 text-center space-y-3">
          <Radio className="h-10 w-10 text-slate-400 mx-auto animate-pulse" />
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">No Devices Paired Yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            You don't have any SafeGas devices linked to your account. Pair a physical ESP32 or enter your device serial ID.
          </p>
          <Button onClick={() => setShowPairModal(true)} leftIcon={<Plus className="h-4 w-4" />} className="mt-2">
            Pair New Device
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {devices.map((device) => (
            <Card key={device.id} className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200">
                    <Radio className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">{device.name}</h3>
                    <p className="text-[11px] font-mono text-slate-400">{device.id}</p>
                  </div>
                </div>
                {deviceStatusBadge(device.status)}
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs bg-slate-50 dark:bg-slate-700/40 p-3 rounded-xl">
                <div>
                  <span className="text-slate-400 block text-[10px]">Firmware</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">v{device.firmware_version}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] flex items-center gap-1">
                    <Wifi className="h-3 w-3 text-blue-500" /> WiFi Signal
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{device.signal_strength}%</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] flex items-center gap-1">
                    <Battery className="h-3 w-3 text-green-500" /> Battery
                  </span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{device.battery_level}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/60 text-xs">
                <span className="text-slate-400 text-[11px]">
                  Paired: {new Date(device.paired_at).toLocaleDateString()}
                </span>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRemoveDevice(device.id)}
                    className="h-8 text-danger hover:bg-red-50 dark:hover:bg-red-950/30"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add / Pair Device Modal */}
      <Modal
        isOpen={showPairModal}
        onClose={() => setShowPairModal(false)}
        title="Pair New ESP32 Device"
        description="Enter the unique device serial code printed on your SafeGas hardware unit."
      >
        <form onSubmit={handlePairDevice} className="space-y-4">
          <Input
            label="Device MAC / Serial ID"
            value={newDeviceId}
            onChange={(e) => setNewDeviceId(e.target.value)}
            placeholder="e.g. SGD-003-ESP32"
            required
          />

          <Input
            label="Device Friendly Name"
            value={newDeviceName}
            onChange={(e) => setNewDeviceName(e.target.value)}
            placeholder="e.g. Main Kitchen Sensor"
            required
          />

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/40 text-xs text-slate-500">
            Ensure your ESP32 device is powered on and connected to 2.4GHz WiFi.
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => setShowPairModal(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isPairing}>Pair Device</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
