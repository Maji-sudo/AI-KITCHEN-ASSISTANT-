import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { LoadingScreen } from '@/components/ui/Loader'
import { MainLayout } from '@/components/layout/MainLayout'

import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
import { Safety } from '@/pages/Safety'
import { Analytics } from '@/pages/Analytics'
import { Cylinder } from '@/pages/Cylinder'
import { CookingAssistant } from '@/pages/CookingAssistant'
import { Recommendations } from '@/pages/Recommendations'
import { Efficiency } from '@/pages/Efficiency'
import { Devices } from '@/pages/Devices'
import { Notifications } from '@/pages/Notifications'
import { Settings } from '@/pages/Settings'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen text="Authenticating SafeGas AI..." />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="safety" element={<Safety />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="cylinder" element={<Cylinder />} />
        <Route path="cooking" element={<CookingAssistant />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="efficiency" element={<Efficiency />} />
        <Route path="devices" element={<Devices />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
