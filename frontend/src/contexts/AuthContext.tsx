import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { User } from '@/types'
import { authService, type AuthResponse, type RegisterPayload, type LoginPayload } from '@/services/auth.service'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<AuthResponse>
  register: (payload: RegisterPayload) => Promise<AuthResponse>
  updatePhone: (phone: string) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

// queryClient reset function — injected from App.tsx so AuthContext
// doesn't need to import QueryClient directly.
let _resetQueryCache: (() => void) | null = null
export function setQueryCacheResetter(fn: () => void) {
  _resetQueryCache = fn
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount: if we have a stored token, validate it against the real backend
  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const me = await authService.getMe()
      setUser(me)
    } catch {
      // Token invalid or expired — clear everything
      authService.logout()
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadUser() }, [loadUser])

  const login = async (payload: LoginPayload): Promise<AuthResponse> => {
    const res = await authService.login(payload)
    const me = await authService.getMe()
    setUser(me)
    return res
  }

  const register = async (payload: RegisterPayload): Promise<AuthResponse> => {
    const res = await authService.register(payload)
    const me = await authService.getMe()
    setUser(me)
    return res
  }

  const updatePhone = async (phone: string): Promise<User> => {
    const updatedUser = await authService.updatePhone(phone)
    setUser(updatedUser)
    return updatedUser
  }

  const logout = () => {
    // 1. Clear stored token + user cache
    authService.logout()
    // 2. Wipe React Query cache so the next user never sees stale data
    if (_resetQueryCache) _resetQueryCache()
    // 3. Clear React state → ProtectedRoute redirects to /login
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, register, updatePhone, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
