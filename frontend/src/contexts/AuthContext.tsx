import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { User } from '@/types'
import { authService } from '@/services/auth.service'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (phone: string, otp: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) { setIsLoading(false); return }
    try {
      const me = await authService.getMe()
      setUser(me)
    } catch {
      localStorage.clear()
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadUser() }, [loadUser])

  const login = async (phone: string, otp: string) => {
    // ── Demo mode bypass ──────────────────────────────────────────────────
    // If the user enters the demo OTP (123456) we skip the real API call
    // and stub out a local demo session so the app works without a backend.
    if (otp === '123456') {
      localStorage.setItem('access_token', 'demo-token')
      localStorage.setItem('user_name', 'Demo User')
      localStorage.setItem('user_id', '0')
      const me = await authService.getMe()
      setUser(me)
      return
    }
    // ─────────────────────────────────────────────────────────────────────
    await authService.verifyOTP({ phone, otp })
    const me = await authService.getMe()
    setUser(me)
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
